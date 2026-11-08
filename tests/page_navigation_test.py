# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for page metadata, navigation, and UI state."""

import subprocess
import unittest
from unittest.mock import patch

from PySide6.QtGui import QFont

from app import MainWindow
from qt_test_utils import APPLICATION


class PageNavigationTest(unittest.TestCase):
    """Verify page controls and page metadata handling."""

    def setUp(self):
        self.application = APPLICATION
        self.window = MainWindow()
        self.window.pdf_path = "document.pdf"
        self.window.total_pages = 4
        self.window.current_page = 1

    def test_display_error_shows_red_message_in_viewer(self):
        self.window.display_error("Unable to load document")

        self.assertEqual(self.window.viewer.text(), "Unable to load document")
        self.assertEqual(self.window.viewer.styleSheet(), "color: red;")
        self.assertEqual(self.window.viewer.font().pointSize(), QFont("Arial", 12).pointSize())

    @patch("app.QFileDialog.getOpenFileName", return_value=("", ""))
    @patch.object(MainWindow, "get_pdf_info")
    @patch.object(MainWindow, "render_page")
    def test_open_pdf_cancel_does_not_change_document(self, render_page, get_pdf_info, _dialog):
        self.window.pdf_path = "existing.pdf"
        self.window.current_page = 2

        self.window.open_pdf()

        self.assertEqual(self.window.pdf_path, "existing.pdf")
        self.assertEqual(self.window.current_page, 2)
        get_pdf_info.assert_not_called()
        render_page.assert_not_called()

    @patch("app.QFileDialog.getOpenFileName", return_value=("new.pdf", "PDF Files (*.pdf)"))
    @patch.object(MainWindow, "get_pdf_info", return_value=True)
    @patch.object(MainWindow, "render_page")
    def test_open_pdf_loads_first_page_after_reading_metadata(
            self, render_page, get_pdf_info, _dialog):
        self.window.current_page = 3

        self.window.open_pdf()

        self.assertEqual(self.window.pdf_path, "new.pdf")
        self.assertEqual(self.window.current_page, 0)
        get_pdf_info.assert_called_once_with()
        render_page.assert_called_once_with()

    @patch("app.QFileDialog.getOpenFileName", return_value=("broken.pdf", "PDF Files (*.pdf)"))
    @patch.object(MainWindow, "get_pdf_info", return_value=False)
    @patch.object(MainWindow, "render_page")
    def test_open_pdf_does_not_render_when_metadata_fails(
            self, render_page, get_pdf_info, _dialog):
        self.window.open_pdf()

        self.assertEqual(self.window.pdf_path, "broken.pdf")
        get_pdf_info.assert_called_once_with()
        render_page.assert_not_called()

    @patch("app.subprocess.run")
    def test_get_pdf_info_parses_page_count(self, run):
        run.return_value.stdout = "Title: Example\nPages: 4\n"

        self.assertTrue(self.window.get_pdf_info())
        self.assertEqual(self.window.total_pages, 4)
        run.assert_called_once_with(
            ["pdfinfo", "document.pdf"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="ignore",
        )

    @patch("app.subprocess.run")
    def test_get_pdf_info_reports_missing_poppler(self, run):
        run.side_effect = FileNotFoundError
        with patch.object(self.window, "display_error") as display_error:
            self.assertFalse(self.window.get_pdf_info())

        display_error.assert_called_once_with("Error: `pdfinfo` command not found.")

    @patch("app.subprocess.run")
    def test_get_pdf_info_reports_invalid_pdf(self, run):
        run.side_effect = subprocess.CalledProcessError(
            1, ["pdfinfo"], stderr="invalid PDF")
        with patch.object(self.window, "display_error") as display_error:
            self.assertFalse(self.window.get_pdf_info())

        self.assertIn("invalid PDF", display_error.call_args.args[0])

    @patch("app.subprocess.run")
    def test_update_page_size_parses_points(self, run):
        run.return_value.stdout = "Page 2 size: 612 x 792 pts (letter)\n"
        run.return_value.stderr = ""

        self.window.update_page_size()

        self.assertEqual(self.window.page_size_points, (612.0, 792.0))
        self.assertEqual(run.call_args.args[0], [
            "pdfinfo", "-f", "2", "-l", "2", "document.pdf",
        ])

    @patch("app.subprocess.run")
    def test_update_page_size_resets_when_no_page_size_is_reported(self, run):
        run.return_value.stdout = "Pages: 4\n"
        run.return_value.stderr = ""
        self.window.page_size_points = (100.0, 200.0)

        self.window.update_page_size()

        self.assertEqual(self.window.page_size_points, (0, 0))

    @patch.object(MainWindow, "render_page")
    def test_next_page_advances_and_renders(self, render_page):
        self.window.next_page()

        self.assertEqual(self.window.current_page, 2)
        render_page.assert_called_once_with()

    @patch.object(MainWindow, "render_page")
    def test_previous_page_decrements_and_renders(self, render_page):
        self.window.prev_page()

        self.assertEqual(self.window.current_page, 0)
        render_page.assert_called_once_with()

    @patch.object(MainWindow, "render_page")
    def test_navigation_does_not_cross_page_bounds(self, render_page):
        self.window.current_page = 0
        self.window.prev_page()
        self.window.current_page = self.window.total_pages - 1
        self.window.next_page()

        self.assertEqual(self.window.current_page, 3)
        render_page.assert_not_called()

    @patch.object(MainWindow, "render_page")
    def test_jump_to_page_uses_one_based_input(self, render_page):
        self.window.txt_page_num.setText("4")

        self.window.jump_to_page()

        self.assertEqual(self.window.current_page, 3)
        render_page.assert_called_once_with()

    @patch.object(MainWindow, "render_page")
    def test_jump_to_invalid_or_out_of_range_page_restores_current_page(self, render_page):
        for value in ("0", "5", "not a number"):
            with self.subTest(value=value):
                self.window.txt_page_num.setText(value)
                self.window.jump_to_page()
                self.assertEqual(self.window.txt_page_num.text(), "2")

        self.assertEqual(self.window.current_page, 1)
        render_page.assert_not_called()

    def test_update_ui_state_updates_page_labels_and_controls(self):
        self.window.current_page = 1

        self.window.update_ui_state()

        self.assertEqual(self.window.txt_page_num.text(), "2")
        self.assertEqual(self.window.lbl_total_pages.text(), " / 4")
        self.assertTrue(self.window.btn_prev.isEnabled())
        self.assertTrue(self.window.btn_next.isEnabled())
        self.assertTrue(self.window.btn_save.isEnabled())
        self.assertTrue(self.window.txt_page_num.isEnabled())

    def test_update_ui_state_disables_boundary_navigation(self):
        self.window.current_page = 0

        self.window.update_ui_state()

        self.assertFalse(self.window.btn_prev.isEnabled())
        self.assertTrue(self.window.btn_next.isEnabled())

        self.window.current_page = self.window.total_pages - 1
        self.window.update_ui_state()

        self.assertTrue(self.window.btn_prev.isEnabled())
        self.assertFalse(self.window.btn_next.isEnabled())


if __name__ == "__main__":
    unittest.main()

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
"""Tests for PDF rendering, SVG export, and temporary-file cleanup."""

import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap

from app import MainWindow
from qt_test_utils import APPLICATION


class PdfWorkflowTest(unittest.TestCase):
    """Exercise PDF processing while replacing external tools with mocks."""

    def setUp(self):
        self.application = APPLICATION
        self.window = MainWindow()
        self.window.pdf_path = "document.pdf"
        self.window.current_page = 1
        self.window.total_pages = 3
        self.window.temp_image_base = "test-preview"

    def test_render_page_builds_expected_poppler_command_and_updates_ui(self):
        process_result = SimpleNamespace(stderr=b"")
        preview_pixmap = QPixmap(80, 120)
        with (
            patch.object(self.window, "update_page_size") as update_size,
            patch.object(self.window, "cleanup_temp_files") as cleanup,
            patch("app.subprocess.run", return_value=process_result) as run,
            patch("app.os.path.exists", return_value=True),
            patch("app.QPixmap", return_value=preview_pixmap),
        ):
            self.window.render_page()

        update_size.assert_called_once_with()
        self.assertEqual(run.call_args.args[0], [
            "pdftoppm", "-f", "2", "-l", "2", "-png", "-r", "150",
            "-singlefile", "document.pdf", "test-preview-2",
        ])
        self.assertTrue(run.call_args.kwargs["check"])
        self.assertEqual(self.window.viewer.pixmap().size(), preview_pixmap.size())
        self.assertTrue(self.window.btn_save.isEnabled())
        self.assertEqual(cleanup.call_count, 2)

    def test_render_page_shows_error_when_rendered_image_is_missing(self):
        with (
            patch.object(self.window, "update_page_size"),
            patch.object(self.window, "cleanup_temp_files"),
            patch.object(self.window, "display_error") as display_error,
            patch("app.subprocess.run", return_value=SimpleNamespace(stderr=b"")),
            patch("app.os.path.exists", return_value=False),
        ):
            self.window.render_page()

        self.assertIn("did not create expected file", display_error.call_args.args[0])

    def test_render_page_shows_poppler_failure(self):
        failure = subprocess.CalledProcessError(
            1, ["pdftoppm"], stderr=b"render failed")
        with (
            patch.object(self.window, "update_page_size"),
            patch.object(self.window, "cleanup_temp_files"),
            patch.object(self.window, "display_error") as display_error,
            patch("app.subprocess.run", side_effect=failure),
        ):
            self.window.render_page()

        self.assertIn("render failed", display_error.call_args.args[0])

    def test_render_page_reports_missing_poppler(self):
        with (
            patch.object(self.window, "update_page_size"),
            patch.object(self.window, "cleanup_temp_files"),
            patch.object(self.window, "display_error") as display_error,
            patch("app.subprocess.run", side_effect=FileNotFoundError),
        ):
            self.window.render_page()

        self.assertIn("Failed to render page 2", display_error.call_args.args[0])

    def test_render_page_without_pdf_path_does_nothing(self):
        self.window.pdf_path = ""
        with patch("app.subprocess.run") as run:
            self.window.render_page()

        run.assert_not_called()

    def test_save_svg_maps_selection_pixels_to_pdf_points(self):
        self.window.viewer.setPixmap(QPixmap(100, 200))
        self.window.viewer.selection_rect = QRect(10, 20, 30, 40)
        self.window.page_size_points = (200.0, 400.0)
        with (
            patch("app.QFileDialog.getSaveFileName", return_value=("crop.svg", "")),
            patch("app.subprocess.run", return_value=SimpleNamespace(stderr="")) as run,
        ):
            self.window.save_svg()

        command = run.call_args.args[0]
        self.assertEqual(command, [
            "pdftocairo", "-svg", "-f", "2", "-l", "2",
            "-x", "20", "-y", "40", "-W", "60", "-H", "80",
            "-paperw", "60", "-paperh", "80", "-nocenter",
            "document.pdf", "crop.svg",
        ])
        self.assertIn("Successfully saved to crop.svg",
                      self.window.statusBar().currentMessage())

    def test_save_svg_ignores_invalid_selection(self):
        with patch("app.QFileDialog.getSaveFileName") as save_dialog, \
                patch("app.subprocess.run") as run:
            self.window.save_svg()

        save_dialog.assert_not_called()
        run.assert_not_called()
        self.assertIn("valid region", self.window.statusBar().currentMessage())

    def test_save_svg_does_nothing_when_save_dialog_is_cancelled(self):
        self.window.viewer.selection_rect = QRect(10, 20, 30, 40)
        with patch("app.QFileDialog.getSaveFileName", return_value=("", "")), \
                patch("app.subprocess.run") as run:
            self.window.save_svg()

        run.assert_not_called()

    def test_save_svg_reports_missing_page_image(self):
        self.window.viewer.selection_rect = QRect(10, 20, 30, 40)
        with patch("app.QFileDialog.getSaveFileName", return_value=("crop.svg", "")), \
                patch("app.subprocess.run") as run:
            self.window.save_svg()

        run.assert_not_called()
        self.assertIn("No page rendered", self.window.statusBar().currentMessage())

    def test_save_svg_reports_poppler_failure(self):
        self.set_valid_export_state()
        failure = subprocess.CalledProcessError(
            1, ["pdftocairo"], stderr="crop failed")
        with patch("app.QFileDialog.getSaveFileName", return_value=("crop.svg", "")), \
                patch("app.subprocess.run", side_effect=failure):
            self.window.save_svg()

        self.assertIn("crop failed", self.window.statusBar().currentMessage())

    def test_save_svg_reports_missing_poppler(self):
        self.set_valid_export_state()
        with patch("app.QFileDialog.getSaveFileName", return_value=("crop.svg", "")), \
                patch("app.subprocess.run", side_effect=FileNotFoundError):
            self.window.save_svg()

        self.assertIn("pdftocairo", self.window.statusBar().currentMessage())

    def test_cleanup_removes_only_matching_pngs(self):
        with patch("app.os.listdir", return_value=[
            "test-preview-1.png",
            "test-preview-2.png",
            "test-preview-not-image.svg",
            "other-preview.png",
        ]), patch("app.os.remove") as remove:
            self.window.cleanup_temp_files()

        self.assertEqual(remove.call_args_list, [
            call("test-preview-1.png"),
            call("test-preview-2.png"),
        ])

    def set_valid_export_state(self):
        """Set a non-empty page image and valid dimensions for export tests."""
        self.window.viewer.setPixmap(QPixmap(100, 200))
        self.window.viewer.selection_rect = QRect(10, 20, 30, 40)
        self.window.page_size_points = (200.0, 400.0)


if __name__ == "__main__":
    unittest.main()

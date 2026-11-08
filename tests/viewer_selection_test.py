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
"""Tests for creating and moving a selection rectangle."""

import unittest

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPixmap

from app import PDFViewerLabel
from qt_test_utils import drag


class ViewerSelectionTest(unittest.TestCase):
    """Verify selection creation and movement through mouse events."""

    def setUp(self):
        self.viewer = PDFViewerLabel()
        self.viewer.setFixedSize(100, 100)
        self.viewer.setPixmap(QPixmap(100, 100))

    def test_creates_selection_when_dragging_down_and_right(self):
        drag(self.viewer, QPoint(10, 15), QPoint(40, 55))

        self.assertEqual(self.viewer.selection_rect, QRect(10, 15, 31, 41))
        self.assertFalse(self.viewer.is_selecting)

    def test_creates_normalized_selection_when_dragging_up_and_left(self):
        drag(self.viewer, QPoint(40, 55), QPoint(10, 15))

        self.assertEqual(self.viewer.selection_rect, QRect(10, 15, 31, 41))

    def test_dragging_inside_selection_moves_it(self):
        self.viewer.selection_rect = QRect(20, 20, 30, 30)

        drag(self.viewer, QPoint(30, 30), QPoint(45, 42))

        self.assertEqual(self.viewer.selection_rect.topLeft(), QPoint(35, 32))
        self.assertFalse(self.viewer.is_selection_moving)

    def test_move_is_clamped_to_page_bounds(self):
        self.viewer.selection_rect = QRect(20, 20, 30, 30)

        drag(self.viewer, QPoint(30, 30), QPoint(95, 95))

        self.assertEqual(self.viewer.selection_rect.topLeft(), QPoint(70, 70))
        self.assertEqual(self.viewer.selection_rect.bottomRight(), QPoint(99, 99))


if __name__ == "__main__":
    unittest.main()

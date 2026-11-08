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
"""Unit tests for resizing the native selection rectangle."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app import PDFViewerLabel  # noqa: E402


class SelectionResizeTest(unittest.TestCase):
    """Exercise selection resizing through the viewer's mouse handlers."""

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.viewer = PDFViewerLabel()
        self.viewer.setFixedSize(100, 100)
        self.viewer.setPixmap(QPixmap(100, 100))
        self.viewer.selection_rect = self.rect(20, 20, 40, 30)

    @staticmethod
    def rect(x, y, width, height):
        return QRect(x, y, width, height)

    def drag(self, start, end):
        """Send a left-button drag directly to the widget event handlers."""
        self.viewer.mousePressEvent(self.mouse_event(
            QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton))
        self.viewer.mouseMoveEvent(self.mouse_event(
            QEvent.Type.MouseMove, end, Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton))
        self.viewer.mouseReleaseEvent(self.mouse_event(
            QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton))

    @staticmethod
    def mouse_event(event_type, position, button, buttons):
        local_position = QPointF(position)
        # The constructor without a global position is deprecated in Qt 6.4+.
        return QMouseEvent(event_type, local_position, local_position, button,
                           buttons, Qt.KeyboardModifier.NoModifier)

    def test_resizes_right_edge(self):
        self.drag(QPoint(59, 34), QPoint(70, 34))

        self.assertEqual(self.viewer.selection_rect.left(), 20)
        self.assertEqual(self.viewer.selection_rect.right(), 70)
        self.assertEqual(self.viewer.selection_rect.height(), 30)

    def test_resizes_bottom_right_corner(self):
        self.drag(QPoint(59, 49), QPoint(70, 60))

        self.assertEqual(self.viewer.selection_rect.topLeft(), QPoint(20, 20))
        self.assertEqual(self.viewer.selection_rect.bottomRight(), QPoint(70, 60))

    def test_clamps_resize_to_image_bounds(self):
        self.drag(QPoint(59, 34), QPoint(150, 34))

        self.assertEqual(self.viewer.selection_rect.right(), 99)
        self.assertEqual(self.viewer.selection_rect.left(), 20)


if __name__ == "__main__":
    unittest.main()

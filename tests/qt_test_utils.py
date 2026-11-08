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
"""Shared helpers for headless Qt unit tests."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


APPLICATION = QApplication.instance() or QApplication([])


def mouse_event(event_type, position, button, buttons):
    """Build a mouse event using Qt's non-deprecated constructor."""
    local_position = QPointF(position)
    return QMouseEvent(
        event_type,
        local_position,
        local_position,
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )


def drag(widget, start, end):
    """Send a left-button press, move, and release to a widget."""
    widget.mousePressEvent(mouse_event(
        QEvent.Type.MouseButtonPress,
        start,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
    ))
    widget.mouseMoveEvent(mouse_event(
        QEvent.Type.MouseMove,
        end,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
    ))
    widget.mouseReleaseEvent(mouse_event(
        QEvent.Type.MouseButtonRelease,
        end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
    ))

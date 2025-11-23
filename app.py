#!/usr/bin/python
#
# Copyright 2025 Google LLC
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
"""Qt application to view PDFs and extract regions to SVG.

Sample applications include extracting charts, graphs, model architectures,
algorithms, equations, etc. from PDFs to share them via blog posts or social
media such that they remain clear and scalable vector graphics, as opposed to
pixelated raster images.

Before using, please see these instructions to install necessary dependencies:
https://github.com/mbrukman/pdf-extract-svg?tab=readme-ov-file#installation
"""

import os
import re
import subprocess
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRect, QPoint, QSize


# DPI for the preview image. Higher values are clearer but use more memory.
PREVIEW_DPI = 150


class PDFViewerLabel(QLabel):
    """
    A custom QLabel to display the PDF page and handle mouse events for selection.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.selection_rect = QRect()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False

    def mousePressEvent(self, event): # pylint: disable=invalid-name
        """Handle mouse click to start the selection."""
        if event.button() == Qt.LeftButton:
            self.start_point = event.position().toPoint()
            self.selection_rect = QRect(self.start_point, QSize())
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event): # pylint: disable=invalid-name
        """Handle mouse drag while selection is in progress."""
        if self.is_selecting:
            self.end_point = event.position().toPoint()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update() # Trigger a repaint

    def mouseReleaseEvent(self, event): # pylint: disable=invalid-name
        """Handle mouse button release while making a selection."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.update()

    def paintEvent(self, event): # pylint: disable=invalid-name
        """Draw the selected region on top of the rendered PDF page."""
        super().paintEvent(event) # Draw the pixmap first

        # Draw the selection box if available (both during dragging and after).
        if not self.selection_rect.isNull():
            painter = QPainter(self)
            pen = QPen(QColor(0, 120, 215, 200), 2, Qt.SolidLine)
            painter.setPen(pen)

            fill_color = QColor(0, 120, 215, 50)
            painter.fillRect(self.selection_rect, fill_color)
            painter.drawRect(self.selection_rect)


class MainWindow(QMainWindow):
    """Handles the UI of the application."""

    def __init__(self):
        """Initialize the UI elements and connect them to handlers."""

        super().__init__()
        self.setWindowTitle("PDF Vector Extractor")
        self.setGeometry(100, 100, 1000, 800)

        # Member variables
        self.pdf_path = None
        self.temp_image_base = "pdf_extractor_temp_page"
        self.current_page = 0
        self.total_pages = 0
        self.page_size_points = (0, 0) # Store page size in points (w, h)

        # --- UI Setup ---
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()

        self.btn_open = QPushButton("Open PDF")
        self.btn_prev = QPushButton("<< Prev")
        self.btn_next = QPushButton("Next >>")
        self.lbl_page = QLabel("Page: N/A")
        self.btn_save = QPushButton("Save Region as SVG")

        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_save.setEnabled(False)

        control_layout.addWidget(self.btn_open)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_prev)
        control_layout.addWidget(self.lbl_page)
        control_layout.addWidget(self.btn_next)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_save)

        # Scrollable area for the PDF viewer
        self.scroll_area = QScrollArea()
        # Allow the widget to be larger than the viewport, enabling scrolling.
        self.scroll_area.setWidgetResizable(False)
        # A dark background makes the page stand out, using a stylesheet.
        self.scroll_area.setStyleSheet("background-color: #3c3c3c;")

        # Custom label for viewing and selection
        self.viewer = PDFViewerLabel()
        self.viewer.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.viewer)

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.scroll_area)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Connections ---
        self.btn_open.clicked.connect(self.open_pdf)
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        self.btn_save.clicked.connect(self.save_svg)

    def display_error(self, message):
        """Helper to display error messages in the viewer."""
        self.viewer.clear()
        self.viewer.setText(message)
        self.viewer.setFont(QFont("Arial", 12))
        self.viewer.setStyleSheet("color: red;")

    def open_pdf(self):
        """Tries to open a PDF and, if successful, renders the first page."""
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            self.pdf_path = path
            self.current_page = 0
            if self.get_pdf_info():
                self.render_page()

    def get_pdf_info(self) -> bool:
        """Gets total pages using pdfinfo and returns status."""
        try:
            command = [
                "pdfinfo",
                self.pdf_path,
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, encoding='utf-8',
                errors='ignore',
            )
            for line in result.stdout.splitlines():
                if "Pages:" in line:
                    self.total_pages = int(line.split(":")[1].strip())
            return True
        except FileNotFoundError:
            self.display_error("Error: `pdfinfo` command not found.")
            return False
        except subprocess.CalledProcessError as e:
            self.display_error(f"Failed to get PDF info.\n"
                               f"PDF may be corrupted or encrypted.\n\n"
                               f"Poppler Error:\n{e.stderr}")
            return False

    def update_page_size(self):
        """Updates the size in points for the current page."""
        try:
            command = [
                "pdfinfo",
                "-f", str(self.current_page + 1),
                "-l", str(self.current_page + 1),
                self.pdf_path
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, encoding='utf-8',
                errors='ignore',
            )
            if result.stderr:
                print(f'pdfinfo warnings: {result.stderr}', file=sys.stderr)
            for line in result.stdout.splitlines():
                # Line format: "Page (page number) size: (width) x (height) pts"
                match = re.match(r'Page\s+\d+\s+size:\s+([\d\.]+)\s+x\s+([\d\.]+)\s+', line)
                if match:
                    width = float(match.group(1))
                    height = float(match.group(2))
                    self.page_size_points = (width, height)
                    return
            self.page_size_points = (0, 0)
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
            print(f"Could not get page size for page {self.current_page + 1}: {e}", file=sys.stderr)
            self.page_size_points = (0, 0)

    def render_page(self):
        """Render a single page from a PDF to a file and display it."""
        if not self.pdf_path:
            return

        self.update_page_size()
        temp_image_path = f"{self.temp_image_base}-{self.current_page + 1}"

        # Clean up old temp files before creating a new one
        self.cleanup_temp_files()

        try:
            # Use pdftoppm to render the current page to a PNG
            command = [
                "pdftoppm",
                "-f", str(self.current_page + 1),
                "-l", str(self.current_page + 1),
                "-png",
                "-r", str(PREVIEW_DPI),
                "-singlefile",
                self.pdf_path,
                temp_image_path, # pdftoppm appends ".png"
            ]
            result = subprocess.run(command, check=True, capture_output=True)

            if result.stderr:
                print(f"pdftoppm warnings:\n{result.stderr}", file=sys.stderr)

            generated_file = temp_image_path + ".png"
            if os.path.exists(generated_file):
                pixmap = QPixmap(generated_file)
                self.viewer.setStyleSheet("") # Reset stylesheet
                self.viewer.setPixmap(pixmap)
                self.viewer.adjustSize() # Resize the label to fit the pixmap
            else:
                raise FileNotFoundError(f"pdftoppm did not create expected file: {generated_file}")

            self.update_ui_state()

        except subprocess.CalledProcessError as e:
            self.display_error(f"Failed to render page {self.current_page + 1}.\n\n"
                               f"Poppler Error:\n{e.stderr.decode('utf-8', 'ignore')}")
        except (FileNotFoundError) as e:
            self.display_error(f"Failed to render page {self.current_page + 1}.\nError: {e}")
        finally:
            # Clean up the generated PNG immediately after loading it
            self.cleanup_temp_files()


    def update_ui_state(self):
        """Enable/disable buttons based on current state."""
        self.lbl_page.setText(f"Page: {self.current_page + 1} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)
        self.btn_save.setEnabled(True)

    def prev_page(self):
        """Move to the previous page in this file, if we're not at the beginning."""
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        """Move to the next page in this file, if we're not at the end."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()

    def save_svg(self):
        """Write selected region to an SVG."""
        selection = self.viewer.selection_rect
        if selection.isNull() or selection.width() < 2 or selection.height() < 2:
            self.statusBar().showMessage("Please select a valid region first.", 3000)
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG Files (*.svg)")
        if not output_path:
            return

        # --- Coordinate Conversion ---
        pixmap = self.viewer.pixmap()
        if not pixmap or pixmap.isNull():
            self.statusBar().showMessage("Cannot save: No page rendered.", 4000)
            return

        pixmap_size = pixmap.size()
        pdf_w_pt, pdf_h_pt = self.page_size_points

        if pixmap_size.width() == 0 or pixmap_size.height() == 0:
            self.statusBar().showMessage("Cannot save: Invalid page dimensions.", 4000)
            return

        # Calculate the scale factor
        scale_x = pdf_w_pt / pixmap_size.width()
        scale_y = pdf_h_pt / pixmap_size.height()

        # Apply the scale to the selection rectangle
        x_pt = selection.x() * scale_x
        y_pt = selection.y() * scale_y
        w_pt = selection.width() * scale_x
        h_pt = selection.height() * scale_y

        # --- Run pdftocairo to extract the SVG ---
        try:
            command = [
                "pdftocairo",
                "-svg",
                "-f", str(self.current_page + 1),
                "-l", str(self.current_page + 1),
                "-x", f'{int(x_pt)}', # Needs to be integer valued!
                "-y", f'{int(y_pt)}', # Needs to be integer valued!
                "-W", f'{int(w_pt)}', # Needs to be integer valued!
                "-H", f'{int(h_pt)}', # Needs to be integer valued!
                "-nocenter",
                "-noshrink",
                self.pdf_path,
                output_path,
            ]
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, encoding='utf-8',
                errors='ignore',
            )

            # Check stderr for warnings even if the command succeeds
            if result.stderr:
                print(f"pdftocairo warnings:\n{result.stderr}", file=sys.stderr)
                self.statusBar().showMessage("Saved with warnings. See console for details.", 5000)
            else:
                self.statusBar().showMessage(f"Successfully saved to {output_path}", 5000)

        except subprocess.CalledProcessError as e:
            # The error you are seeing will be caught here
            print(f"Error saving SVG: {e.stderr.strip()}", file=sys.stderr)
            self.statusBar().showMessage(f"Error saving SVG: {e.stderr.strip()}", 10000)
        except FileNotFoundError:
            self.statusBar().showMessage("Error: 'pdftocairo' command not found.", 5000)

    def cleanup_temp_files(self):
        """Clean up any temporary image files."""
        for f in os.listdir('.'):
            if f.startswith(self.temp_image_base) and f.endswith(".png"):
                try:
                    os.remove(f)
                except OSError as e:
                    print(f"Error removing temp file {f}: {e}", file=sys.stderr)

    def closeEvent(self, event): # pylint: disable=invalid-name
        """Clean up temporary files on exit."""
        self.cleanup_temp_files()
        super().closeEvent(event)


def main(argv):
    all_tools = ["pdftocairo", "pdftoppm", "pdfinfo"]
    missing_tools = []

    for tool in all_tools:
        try:
            # Use --version to check for existence without processing a file
            subprocess.run([tool, "-v"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)

    if missing_tools:
        print(f"Error: Poppler tools not found: {', '.join(missing_tools)}.\n"
              "Please install 'poppler-utils' and ensure it's in your PATH.\n"
              "More info: "
              "https://github.com/mbrukman/pdf-extract-svg?tab=readme-ov-file#installation",
              file=sys.stderr)
        sys.exit(1)

    app = QApplication(argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main(sys.argv)

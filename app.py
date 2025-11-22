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

import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRect, QPoint, QSize

# --- Configuration ---
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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.selection_rect = QRect(self.start_point, QSize())
            self.is_selecting = True

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update() # Trigger a repaint

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event) # Draw the pixmap first
        if not self.selection_rect.isNull() and self.is_selecting:
            painter = QPainter(self)
            pen = QPen(QColor(0, 120, 215, 200), 2, Qt.SolidLine)
            painter.setPen(pen)

            fill_color = QColor(0, 120, 215, 50)
            painter.fillRect(self.selection_rect, fill_color)
            painter.drawRect(self.selection_rect)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Vector Extractor")
        self.setGeometry(100, 100, 1000, 800)

        # Member variables
        self.pdf_path = None
        self.temp_image_path = "temp_page.png"
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
        self.scroll_area.setWidgetResizable(True)
        # A dark background makes the page stand out. Using a stylesheet is a modern way to do this.
        self.scroll_area.setStyleSheet("background-color: #3c3c3c;")

        # Custom label for viewing and selection
        self.viewer = PDFViewerLabel()
        self.viewer.setAlignment(Qt.AlignCenter)
        self.viewer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
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

        self.check_poppler_tools()

    def check_poppler_tools(self):
        """Checks if Poppler command-line tools are accessible."""
        try:
            # Use --version to check for existence without processing a file
            subprocess.run(["pdftocairo", "-v"], check=True, capture_output=True)
            subprocess.run(["pdftoppm", "-v"], check=True, capture_output=True)
            subprocess.run(["pdfinfo", "-v"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.viewer.setText("Error: Poppler tools not found.\n"
                                "Please install 'poppler-utils' and ensure it's in your system's PATH.")
            self.viewer.setFont(QFont("Arial", 14))
            self.viewer.setStyleSheet("color: red;")
            for btn in [self.btn_open, self.btn_save, self.btn_prev, self.btn_next]:
                btn.setEnabled(False)

    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            self.pdf_path = path
            self.get_pdf_info()
            self.current_page = 0
            self.render_page()

    def get_pdf_info(self):
        """Gets total pages and page dimensions using pdfinfo."""
        try:
            # Get total pages
            result = subprocess.run(["pdfinfo", self.pdf_path], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if "Pages:" in line:
                    self.total_pages = int(line.split(":")[1].strip())

            # Get first page dimensions
            self.update_page_size()
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error getting PDF info: {e}")
            self.total_pages = 0

    def update_page_size(self):
        """Updates the size in points for the current page."""
        try:
            result = subprocess.run(
                ["pdfinfo", "-f", str(self.current_page + 1), "-l", str(self.current_page + 1), self.pdf_path],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                if "Page size:" in line:
                    parts = line.split(":")[1].strip().split("x")
                    width = float(parts[0].strip())
                    height = float(parts[1].split(" ")[0].strip())
                    self.page_size_points = (width, height)
                    break
        except Exception as e:
            print(f"Could not get page size: {e}")
            self.page_size_points = (0, 0)

    def render_page(self):
        if not self.pdf_path:
            return

        self.update_page_size()

        # Use pdftoppm to render the current page to a PNG
        try:
            subprocess.run([
                "pdftoppm",
                "-f", str(self.current_page + 1),
                "-l", str(self.current_page + 1),
                "-png",
                "-r", str(PREVIEW_DPI),
                self.pdf_path,
                self.temp_image_path.replace(".png", "") # pdftoppm appends suffix
            ], check=True)

            # The output file is named like 'temp_page-1.png'
            generated_file = f"{self.temp_image_path.replace('.png', '')}-{self.current_page + 1}.png"
            if not os.path.exists(generated_file):
                # some versions of poppler might not append the page number if only one page is rendered
                generated_file = f"{self.temp_image_path.replace('.png', '')}.png"


            pixmap = QPixmap(generated_file)
            self.viewer.setPixmap(pixmap)
            self.viewer.adjustSize()
            os.remove(generated_file) # Clean up the temp file

            self.update_ui_state()

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.viewer.setText(f"Failed to render page {self.current_page + 1}.\nError: {e}")

    def update_ui_state(self):
        """Enable/disable buttons based on current state."""
        self.lbl_page.setText(f"Page: {self.current_page + 1} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)
        self.btn_save.setEnabled(True)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()

    def save_svg(self):
        selection = self.viewer.selection_rect
        if selection.isNull() or selection.width() == 0 or selection.height() == 0:
            # A simple way to inform user without blocking dialogs
            self.statusBar().showMessage("Please select a region first.", 3000)
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG Files (*.svg)")
        if not output_path:
            return

        # --- Coordinate Conversion ---
        # Convert pixel selection from the rendered image to PDF points
        pixmap_size = self.viewer.pixmap().size()
        pdf_w_pt, pdf_h_pt = self.page_size_points

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
            subprocess.run([
                "pdftocairo",
                "-svg",
                "-f", str(self.current_page + 1),
                "-l", str(self.current_page + 1),
                "-x", str(x_pt),
                "-y", str(y_pt),
                "-W", str(w_pt),
                "-H", str(h_pt),
                self.pdf_path,
                output_path
            ], check=True)
            self.statusBar().showMessage(f"Successfully saved to {output_path}", 5000)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.statusBar().showMessage(f"Error saving SVG: {e}", 5000)

    def closeEvent(self, event):
        """Clean up temporary files on exit."""
        # Find any remaining temp files and remove them
        for f in os.listdir('.'):
            if f.startswith(self.temp_image_path.replace(".png", "")):
                try:
                    os.remove(f)
                except OSError as e:
                    print(f"Error removing temp file {f}: {e}")
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


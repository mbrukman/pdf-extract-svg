// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { optimize as svgOptimize } from "svgo.browser.js";

class PdfCropper {
  constructor() {
    // State
    this.pdfDoc = null;
    this.pageNum = 1;
    this.pageRendering = false;
    this.pageNumPending = null;
    this.scale = 1.5;

    // Selection State
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;
    this.selectionRect = null; // {x, y, w, h} (in canvas pixels)

    // DOM Elements - to be initialized in init()
    this.canvas = null;
    this.ctx = null;
    this.selectionBox = null;
    this.container = null;
  }

  init() {
    // Cache DOM elements
    this.canvas = document.getElementById('pdf-canvas');
    this.ctx = this.canvas.getContext('2d');
    this.selectionBox = document.getElementById('selection-box');
    this.container = document.getElementById('pdf-container');

    this.fileInput = document.getElementById('file-input');
    this.prevBtn = document.getElementById('prev-btn');
    this.nextBtn = document.getElementById('next-btn');
    this.downloadBtn = document.getElementById('download-btn');
    this.pageNumSpan = document.getElementById('page-num');
    this.pageCountSpan = document.getElementById('page-count');
    this.statusText = document.getElementById('status-text');

    // Attach Event Listeners
    this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    this.prevBtn.addEventListener('click', () => this.onPrevPage());
    this.nextBtn.addEventListener('click', () => this.onNextPage());
    this.downloadBtn.addEventListener('click', () => this.handleDownload());

    // Mouse Events for Selection
    this.container.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    this.container.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.container.addEventListener('mouseup', (e) => this.handleMouseUp(e));
  }

  // 1. Handle File Upload
  handleFileUpload(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      const fileReader = new FileReader();
      fileReader.onload = (event) => {
        const typedarray = new Uint8Array(event.target.result);
        this.loadPDF(typedarray).catch((error) => {
          console.error(error);
        });
      };
      fileReader.readAsArrayBuffer(file);
      this.statusText.textContent = "Loading PDF...";
    }
  }

  // 2. Load PDF Document
  async loadPDF(data) {
    try {
      this.pdfDoc = await pdfjsLib.getDocument(data).promise;
      this.pageCountSpan.textContent = this.pdfDoc.numPages;
      this.statusText.textContent = "PDF Loaded. Drag to select region.";

      // Reset State
      this.pageNum = 1;
      this.renderPage(this.pageNum);
      this.updateButtons();
    } catch (err) {
      console.error(err);
      alert('Error loading PDF: ' + err.message);
    }
  }

  // 3. Render Page to Canvas
  async renderPage(num) {
    this.pageRendering = true;

    // Clear previous selection
    this.selectionRect = null;
    this.selectionBox.style.display = 'none';
    this.downloadBtn.disabled = true;

    const page = await this.pdfDoc.getPage(num);
    const viewport = page.getViewport({ scale: this.scale });

    this.canvas.height = viewport.height;
    this.canvas.width = viewport.width;

    const renderContext = {
      canvasContext: this.ctx,
      viewport: viewport,
    };

    const renderTask = page.render(renderContext);

    // Wait for render to finish
    try {
      await renderTask.promise;
      this.pageRendering = false;
      this.pageNumSpan.textContent = num;

      if (this.pageNumPending !== null) {
        this.renderPage(this.pageNumPending);
        this.pageNumPending = null;
      }
    } catch (e) {
      // Render cancelled or failed
      this.pageRendering = false;
    }
  }

  queueRenderPage(num) {
    if (this.pageRendering) {
      this.pageNumPending = num;
    } else {
      this.renderPage(num);
    }
  }

  onPrevPage() {
    if (this.pageNum <= 1) return;
    this.pageNum--;
    this.queueRenderPage(this.pageNum);
    this.updateButtons();
  }

  onNextPage() {
    if (this.pageNum >= this.pdfDoc.numPages) return;
    this.pageNum++;
    this.queueRenderPage(this.pageNum);
    this.updateButtons();
  }

  updateButtons() {
    this.prevBtn.disabled = this.pageNum <= 1;
    this.nextBtn.disabled = this.pageNum >= this.pdfDoc.numPages;
  }

  // 4. Mouse Drag / Selection Logic
  handleMouseDown(e) {
    if (!this.pdfDoc) return;

  // Get mouse position relative to container
    const rect = this.container.getBoundingClientRect();
    this.startX = e.clientX - rect.left;
    this.startY = e.clientY - rect.top;

    this.isDragging = true;

    // Reset visible selection
    this.selectionBox.style.left = this.startX + 'px';
    this.selectionBox.style.top = this.startY + 'px';
    this.selectionBox.style.width = '0px';
    this.selectionBox.style.height = '0px';
    this.selectionBox.style.display = 'block';

    this.downloadBtn.disabled = true;
  }

  handleMouseMove(e) {
    if (!this.isDragging) return;

    const rect = this.container.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    // Calculate width/height allowing for dragging in any direction
    const width = Math.abs(currentX - this.startX);
    const height = Math.abs(currentY - this.startY);
    const left = Math.min(this.startX, currentX);
    const top = Math.min(this.startY, currentY);

    // Update UI
    this.selectionBox.style.left = left + 'px';
    this.selectionBox.style.top = top + 'px';
    this.selectionBox.style.width = width + 'px';
    this.selectionBox.style.height = height + 'px';
  }

  handleMouseUp(e) {
    if (!this.isDragging) return;
    this.isDragging = false;

    // Finalize selection coordinates (in Canvas pixels)
    const style = window.getComputedStyle(this.selectionBox);
    const w = parseFloat(style.width);
    const h = parseFloat(style.height);
    const x = parseFloat(style.left);
    const y = parseFloat(style.top);

    if (w > 5 && h > 5) {
      this.selectionRect = { x, y, w, h };
      this.downloadBtn.disabled = false;
    } else {
      this.selectionBox.style.display = 'none'; // Click without drag
    }
  }

  /**
   * Formats the given SVG string to be well-indented for reading.
   *
   * @param {str} svgString
   * @returns {str} formatted string
   */
  formatXmlString(svgString) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(svgString, "image/svg+xml");
    const indent = "  ";
    let result = "";

    /**
     * Recursively traverses the DOM tree and returns an indented string representing it.
     *
     * @param {Node} node
     * @param {int} level
     */
    const traverse = (node, level) => {
      const indentation = indent.repeat(level);
      if (node.nodeType === Node.ELEMENT_NODE) {
        const attributes = Array.from(node.attributes)
          .map(attr => ` ${attr.name}="${attr.value}"`)
          .join("");

        result += `${indentation}<${node.nodeName}${attributes}`;

        if (node.childNodes.length > 0) {
          result += ">\n";
          node.childNodes.forEach(child => traverse(child, level + 1));
          result += `${indentation}</${node.nodeName}>\n`;
        } else {
          result += " />\n";
        }
      } else if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
        result += indentation + node.textContent.trim() + "\n";
      }
    };

    traverse(doc.documentElement, 0);
    return result;
  }

  // 5. SVG Export Logic
  async handleDownload() {
    if (!this.selectionRect || !this.pdfDoc) return;

    const originalText = this.downloadBtn.textContent;
    this.downloadBtn.textContent = "Generating SVG...";
    this.downloadBtn.disabled = true;

    try {
      const page = await this.pdfDoc.getPage(this.pageNum);

      // 1. Get the OperatorList (The raw PDF drawing commands)
      const operatorList = await page.getOperatorList();

      // 2. Setup SVG Graphics
      const svgGraphics = new pdfjsLib.SVGGraphics(page.commonObjs, page.objs);

      // 3. Render full page to SVG
      const pdfViewport = page.getViewport({ scale: 1.0 });
      const svgElement = await svgGraphics.getSVG(operatorList, pdfViewport);

      // 4. Translate User Selection (Pixels) to PDF Points
      const svgX = this.selectionRect.x / this.scale;
      const svgY = this.selectionRect.y / this.scale;
      const svgW = this.selectionRect.w / this.scale;
      const svgH = this.selectionRect.h / this.scale;

      // 5. Apply the "Crop" using viewBox
      svgElement.setAttribute('viewBox', `${svgX} ${svgY} ${svgW} ${svgH}`);

      // Mirror the PDF aspect ratio size for the display
      svgElement.setAttribute('width', svgW + 'pt');
      svgElement.setAttribute('height', svgH + 'pt');

      // 6. Serialize and Download
      const serializer = new XMLSerializer();
      let rawSvgString = serializer.serializeToString(svgElement);
      let svgString = rawSvgString;

      // Allow optional optimization via URL param.
      const getUrlParamBool = (param) => {
        const urlParams = new URLSearchParams(window.location.search);
        const paramValue = urlParams.get(param);
        return paramValue && (paramValue.toLocaleLowerCase() in ['1', 'true', 'yes']);
      }
      const optimizeWithSvgo = getUrlParamBool('svgopt');

      if (optimizeWithSvgo) {
        console.debug('Optimizing SVG output via SVGO ...');
        const svgoResult = svgOptimize(rawSvgString, {
          plugins: [
            'preset-default',
            'removeOffCanvasPaths',
          ],
        });
        svgString = this.formatXmlString(svgoResult.data);
      }

      const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `page-${this.pageNum}-selection.svg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

    } catch (err) {
      console.error(err);
      alert("Error generating SVG: " + err.message);
    } finally {
      this.downloadBtn.textContent = originalText;
      this.downloadBtn.disabled = false;
    }
  }
}

// Initialize the app and UI bindings once the DOM has loaded.
document.addEventListener('DOMContentLoaded', () => {
  const cropper = new PdfCropper();
  cropper.init();
});

// Initialize PDF.js worker after all <script> tags have been loaded.
window.addEventListener('load', () => {
  window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.js';
});

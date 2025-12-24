# PDF to SVG as a web app

The goal of this prototype is to build a web app to support PDF rendering and
exporting selection to SVG, like the main app at the root of this repo.

> [!WARNING]
> The app currently does not work (see below for details), so this is not ready
> for use by end-users, and is only useful as a proof-of-concept and a starting
> point for developers.

## Table of contents

1. [Current status](#current-status)
2. [Access the hosted app](#access-the-hosted-app)
2. [Run the app locally](#run-the-app-locally)
3. [Known issues](#known-issues)
4. [Potential next steps](#potential-next-steps)

## Current status

At this time, you can:

* load a PDF into the web app
* create a rectangular selection
* export the selection to SVG

Unfortunately, the exported text is often garbled, and the graphics aren't
properly rendering, so this is not usable. At this time, this is just a
prototype and a starting point for potential improvements.

See below for known issues and potential next steps.

## Access the hosted app

To access the hosted app, **visit https://mbrukman.github.io/web/app.html** .

Once it's open:

1. Click "Choose File" to upload a PDF file

2. Navigate to a specific page in your document

   **Note:** only next page / previous page are supported; you cannot jump to a
   specific page in the PDF document.

3. Make a rectangular selection by dragging the mouse

4. Click on the button "Downlaod Selection as SVG"

5. Open the resulting downloaded SVG to observe how well it mathes your
   selection

There is no server-side component, any uploaded data is managed via JavaScript
in your browser.

## Run the app locally

> [!IMPORTANT]
> Due to the use of JS modules, you cannot just open the HTML file directly in
> your browser if you download the code with `file://` protocol; it must be
> opened via `http://` or `https://` prototocol.
>
> If you really want to develop the app without a local web server, you would
> need to:
>
> * Remove all mentions of SVGO, especially the `import` in `app.js`
> * Remove `type="module"` from the `<script>` tag loading `app.js`
>
> That's it.

To run it locally, e.g., for development:

1. Clone the repository:

   ```sh
   git clone https://github.com/mbrukman/pdf-to-svg
   ```

   or download the zip file of the repo from the main repo page.

2. `cd web`

3. Run a local Python server:

   ```sh
   make run PORT=9000
   ```

   This will start a web server on localhost with the given port; omitting it
   will run on the default port specified in the [`Makefile`](Makefile).
   to change the port, run it as follows:

4. Open the printed URL in your browser, e.g., http://localhost:9000/

   **Note:** by default, the web server only supports connections from localhost
   for security; if you're developing on another machine on your network, you
   will not be able to access the page even if you supply the FQDN of the
   machine. To fix this, remove the `--bind 127.0.0.1` flag from the command in
   the `Makefile`.

5. Click "Choose File" to upload a PDF file

6. Navigate to a specific page in your document

   **Note:** only next page / previous page are supported; you cannot jump to a
   specific page in the PDF document.

7. Make a rectangular selection by dragging the mouse

8. Click on the button "Downlaod Selection as SVG"

9. Open the resulting downloaded SVG to observe how well it mathes your
   selection

## Known issues

### SVG backend was deprecated and removed from PDF.js

The last stable version of PDF.js to include SVG as a backend was 3.11.174
(which is what we're using in this prototype).

The following stable version (4.0.189) removed SVG support, so we cannot upgrade
to a later version of PDF.js to get any improvements to the SVG rendering
library, nor file any bugs and expect them to be removed.

The bugs that we have encountered (see above in "Current status") will remain
unfixed.

### PDF.js appears to export the entire page to SVG

It appears that when exporting to SVG, the entire page is exported, and the
viewport is set to the rectangular selection that we have provided, but this
means that the SVG includes more than the user may intend to share with the
recipient.

We added support for [SVGO][svgo], an SVG optimizer, which can be enabled by
adding `svgopt=1` to the URL of the app, but it's unclear if it's actually
removing any element that's outside of the viewport, so you should be aware of
this if you're sharing extracts from any document which contains otherwise
sensitive content.

## Potential next steps

* Find another PDF rendering library that supports SVG output, written in
  JavaScript / TypeScript, so that it's easy to incorporate into a web app.

  **Warning:** some libraries are under licenses that are incompatible with
  Apache 2.0 (which this project is under), so that would cause this app to have
  to change its license as well, which is not an option at this time.
  
  That said, you're welcome to try this out, including forking this code.

* Restore the SVG export in [PDF.js][pdf-js] and fix the existing issues with
  fonts, diagrams, etc. Since it was removed from PDF.js, this would probably
  need to be maintained outside of the PDF.js tree, and added as a plugin to
  work, and require ongoing migrations to support newer versions of PDF.js.
  This is likely a massive undertaking.

* Compile the [Poppler tools][poppler] to WASM to enable using them in a web
  app. This is likely a non-trivial amount of work.

  **Warning:** since Poppler is licensed under GPL, including the generated
  output code as part of the app would likely cause this app to also be licensed
  under the GPL. 

* Compile Chrome's [PDFium][pdfium] library to WASM to use it from the browser;
  however, it doesn't have SVG export, so that would need to be added, but
  Poppler (above) already has SVG support, so that may be an easier option to
  pursue.

Any other options? Or maybe you've tried something above and it worked (or
didn't)?

Please feel free to add a note to [this
issue](https://github.com/mbrukman/pdf-extract-svg/issues/31) if you have
thoughts on this. Thanks!

[pdf-js]: https://mozilla.github.io/pdf.js/
[pdfium]: https://pdfium.googlesource.com/pdfium/
[poppler]: https://poppler.freedesktop.org/
[svgo]: https://svgo.dev/

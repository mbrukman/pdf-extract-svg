# Extract vectors from PDF to SVG

[![Lint][pdf-extract-svg-lint-badge]][pdf-extract-svg-lint-url]
[![Typecheck][pdf-extract-svg-typecheck-badge]][pdf-extract-svg-typecheck-url]

[pdf-extract-svg-lint-badge]: https://github.com/mbrukman/pdf-extract-svg/actions/workflows/lint.yaml/badge.svg?branch=main
[pdf-extract-svg-lint-url]: https://github.com/mbrukman/pdf-extract-svg/actions/workflows/lint.yaml?query=branch%3Amain
[pdf-extract-svg-typecheck-badge]: https://github.com/mbrukman/pdf-extract-svg/actions/workflows/typecheck.yaml/badge.svg?branch=main
[pdf-extract-svg-typecheck-url]: https://github.com/mbrukman/pdf-extract-svg/actions/workflows/typecheck.yaml?query=branch%3Amain

This app enables extracting regions in a PDF file, such as a diagram, or chart,
or an algorithm, using the vector data in the PDF into an SVG file, which scales
losslessly.

Typical alternative approaches of extracting diagrams and charts from PDF files
(such as research papers) involve taking a screenshot and converting it to a
raster image such as JPG, PNG, WebP, AVIF, or similar, which unfortunately
become pixelated when zooming in or scaling them larger to examine fine-grained
details.

## Installation

* Install CLI tools for querying and managing PDFs

  The script uses `pdftocairo`, `pdftoppm`, and `pdfinfo`.

  * Debian, Ubuntu, etc.: `sudo apt install poppler-utils`
  * RedHat, Fedora, CentOS, etc.: `sudo dnf install poppler-utils`
  * Other Linux distributions: see [Repology](https://repology.org/project/poppler/versions)
  * macOS: install [Homebrew](https://brew.sh) and `brew install poppler`
  * Other: install [Poppler](https://poppler.freedesktop.org) from source

* Create a Python virtual environment and install necessary Python packages

  ```sh
  # Create a new virtual environment
  python -m venv venv

  # Activate the new environment
  source venv/bin/activate

  # Install necessary Python packages
  python -m pip install -r requirements.txt
  ```

## Run the program

> [!IMPORTANT]
> If you are using virtual environments, you need to use this method of running
> the app.

Start the program via:

```sh
python app.py
```

> [!NOTE]
> If you PySide6 globally and are not using virtual environments, you can just
> run the script itself directly.

```sh
# Implicitly uses /usr/bin/python
./app.py
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).

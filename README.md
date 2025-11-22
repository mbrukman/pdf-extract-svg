# Extract vectors from PDF to SVG

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

  ```sh
  # Debian, Ubuntu, etc.
  sudo apt install poppler-utils

  # RedHat, Fedora, CentOS, etc.
  sudo dnf install poppler-utils
  ```

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

Start the program via either:

```sh
# Implicitly uses /usr/bin/python
./app.py
```

or

```sh
# Use the first `python` binary in your $PATH, or manually choose another one
python app.py
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).

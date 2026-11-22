from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader


class PdfParser:
    """Extract textual content from PDF documents."""

    @staticmethod
    def extract_pages(pdf_source: str | Path | bytes | BinaryIO) -> list[str]:
        # Convert text paths to Path objects so file existence can be validated.
        if isinstance(pdf_source, (str, Path)):
            pdf_path = Path(pdf_source)

            # Stop before opening when the requested PDF cannot be found.
            if not pdf_path.is_file():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            reader = PdfReader(str(pdf_path))
        elif isinstance(pdf_source, bytes):
            # Convert raw bytes into an in-memory binary stream for pypdf.
            reader = PdfReader(BytesIO(pdf_source))
        else:
            # Let pypdf read PDF data supplied as bytes or an open binary stream.
            reader = PdfReader(pdf_source)

        # Extract text independently from every page, preserving page order.
        pages: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                # pypdf returns None for a page that contains no extractable text.
                page_text = page.extract_text()
            except Exception as exc:
                raise RuntimeError(
                    f"Could not extract text from PDF page {page_number}"
                ) from exc
            pages.append(page_text.strip() if page_text else "")

        # Include an entry for every page, including pages with no text.
        return pages

    @classmethod
    def extract_text(cls, pdf_source: str | Path | bytes | BinaryIO) -> str:
        # Extract all pages and join them with page separators.
        pages = cls.extract_pages(pdf_source)
        return "\n\n\f\n\n".join(pages)



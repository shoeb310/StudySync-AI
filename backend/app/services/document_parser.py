import io
import logging
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class DocumentParserError(Exception):
    """Custom exception raised when document parsing encounters an unrecoverable error."""
    pass


class DocumentParser:
    """
    Parser service that extracts raw text from PDF and TXT files
    while preserving page numbers and document metadata.
    """

    @staticmethod
    def parse_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Extract text page-by-page from a PDF file.

        Args:
            file_bytes: Raw binary content of the PDF.
            filename: Source filename for logging and metadata.

        Returns:
            List of dictionaries with 'page_number' (1-indexed) and 'text'.
        """
        pages_content: List[Dict[str, Any]] = []

        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)

            if len(reader.pages) == 0:
                logger.warning(f"PDF file '{filename}' contains 0 pages.")
                return pages_content

            for page_index, page in enumerate(reader.pages):
                page_number = page_index + 1
                try:
                    raw_text = page.extract_text() or ""
                    cleaned_text = " ".join(raw_text.split())

                    if cleaned_text:
                        pages_content.append({
                            "page_number": page_number,
                            "text": cleaned_text
                        })
                    else:
                        logger.info(f"Page {page_number} in '{filename}' had no extractable text (blank or scanned image).")
                except Exception as page_err:
                    logger.warning(f"Error extracting text from page {page_number} of '{filename}': {page_err}")
                    continue

            logger.info(f"Successfully extracted {len(pages_content)} text pages from PDF '{filename}'.")
            return pages_content

        except Exception as exc:
            logger.error(f"Failed to parse PDF '{filename}': {exc}")
            raise DocumentParserError(f"Unable to parse PDF '{filename}': {str(exc)}") from exc

    @staticmethod
    def parse_txt(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parse plain text files. Supports UTF-8 with Latin-1 fallback.

        Args:
            file_bytes: Raw binary content.
            filename: Source filename.

        Returns:
            List with a single page entry containing cleaned text.
        """
        try:
            try:
                decoded_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 decoding failed for '{filename}'. Falling back to latin-1.")
                decoded_text = file_bytes.decode("latin-1")

            cleaned_text = " ".join(decoded_text.split())
            if not cleaned_text:
                return []

            return [{
                "page_number": 1,
                "text": cleaned_text
            }]
        except Exception as exc:
            logger.error(f"Failed to parse TXT file '{filename}': {exc}")
            raise DocumentParserError(f"Unable to parse TXT '{filename}': {str(exc)}") from exc

    @classmethod
    def parse_document(cls, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Dispatch parsing based on file extension.

        Args:
            file_bytes: Binary payload of uploaded file.
            filename: Name of the file with extension.

        Returns:
            List of parsed page objects with page numbers and text.
        """
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return cls.parse_pdf(file_bytes, filename)
        elif lower_name.endswith(".txt"):
            return cls.parse_txt(file_bytes, filename)
        else:
            raise DocumentParserError(f"Unsupported file format for '{filename}'. Only .pdf and .txt are supported.")

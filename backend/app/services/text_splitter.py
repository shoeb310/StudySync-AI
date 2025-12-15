import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RecursiveCharacterTextSplitter:
    """
    Splits long academic text into manageable semantic chunks using a hierarchy
    of separators (paragraphs, newlines, sentences, spaces).
    
    Adheres strictly to the 500-character window with 50-character overlap specification.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""]

    def _split_text_with_separator(self, text: str, separator: str) -> List[str]:
        """Split text using the specified separator while preserving content."""
        if not separator:
            return list(text)
        return text.split(separator)

    def split_text(self, text: str) -> List[str]:
        """
        Recursively break down text until each segment fits within `chunk_size`
        and re-merge segments while honoring `chunk_overlap`.
        """
        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text] if text else []

        # Find appropriate separator
        chosen_separator = self.separators[-1]
        for sep in self.separators:
            if sep == "" or sep in text:
                chosen_separator = sep
                break

        splits = self._split_text_with_separator(text, chosen_separator)

        # Process pieces and combine with overlap
        good_splits: List[str] = []
        for piece in splits:
            if len(piece) <= self.chunk_size:
                if piece:
                    good_splits.append(piece)
            else:
                # Recursively split with remaining separators
                remaining_separators = (
                    self.separators[self.separators.index(chosen_separator) + 1:]
                    if chosen_separator in self.separators
                    else [""]
                )
                sub_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=remaining_separators
                )
                sub_splits = sub_splitter.split_text(piece)
                good_splits.extend(sub_splits)

        # Merge splits into windows of chunk_size with chunk_overlap
        merged_chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for piece in good_splits:
            piece_length = len(piece) + (len(chosen_separator) if current_chunk else 0)

            if current_length + piece_length > self.chunk_size and current_chunk:
                merged_chunk_str = chosen_separator.join(current_chunk).strip()
                if merged_chunk_str:
                    merged_chunks.append(merged_chunk_str)

                # Keep overlap pieces from the tail of current_chunk
                overlap_chunk: List[str] = []
                overlap_length = 0
                for prev_piece in reversed(current_chunk):
                    if overlap_length + len(prev_piece) <= self.chunk_overlap:
                        overlap_chunk.insert(0, prev_piece)
                        overlap_length += len(prev_piece) + len(chosen_separator)
                    else:
                        break

                current_chunk = overlap_chunk
                current_length = sum(len(p) for p in current_chunk) + (
                    len(chosen_separator) * (len(current_chunk) - 1) if current_chunk else 0
                )

            current_chunk.append(piece)
            current_length += len(piece) + (len(chosen_separator) if len(current_chunk) > 1 else 0)

        if current_chunk:
            final_chunk_str = chosen_separator.join(current_chunk).strip()
            if final_chunk_str:
                merged_chunks.append(final_chunk_str)

        return merged_chunks

    def create_chunks(
        self,
        pages: List[Dict[str, Any]],
        notebook_id: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Split parsed pages into enriched chunks containing text and vector metadata.

        Args:
            pages: List of dicts with 'page_number' and 'text'.
            notebook_id: Target notebook identifier.
            filename: Source document filename.

        Returns:
            List of dictionaries formatted for ChromaDB ingestion.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_counter = 0

        # Sanitize filename for chunk_id uniqueness
        safe_filename = re.sub(r"[^\w\-.]", "_", filename)

        for page in pages:
            page_number = page.get("page_number", 1)
            page_text = page.get("text", "")

            if not page_text:
                continue

            text_splits = self.split_text(page_text)
            for split_text in text_splits:
                chunk_counter += 1
                chunk_id = f"{notebook_id}_{safe_filename}_p{page_number}_c{chunk_counter}"

                chunks.append({
                    "chunk_id": chunk_id,
                    "text": split_text,
                    "metadata": {
                        "notebook_id": notebook_id,
                        "filename": filename,
                        "page_number": int(page_number),
                        "chunk_id": chunk_id,
                        "char_count": len(split_text)
                    }
                })

        logger.info(
            f"Created {len(chunks)} chunks (window={self.chunk_size}, overlap={self.chunk_overlap}) "
            f"for '{filename}' in notebook '{notebook_id}'."
        )
        return chunks

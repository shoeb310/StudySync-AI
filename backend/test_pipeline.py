"""
Verification test script for ingestion and embedding pipeline:
- DocumentParser (PDF & TXT extraction)
- RecursiveCharacterTextSplitter (500-char window / 50-char overlap)
- EmbeddingService (768-dimension vectors)
"""
import io
from pypdf import PdfWriter
from app.services.document_parser import DocumentParser
from app.services.text_splitter import RecursiveCharacterTextSplitter
from app.services.embedding_service import EmbeddingService, EMBEDDING_DIMENSION


def test_txt_parser():
    """Verify text file parsing."""
    raw_text = b"StudySync AI is an academic assistant.\nIt organizes documents by notebook."
    pages = DocumentParser.parse_document(raw_text, "notes.txt")
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert "StudySync AI" in pages[0]["text"]
    print(" TXT DocumentParser test PASSED")


def test_text_splitter():
    """Verify recursive character text splitting with 500 window and 50 overlap."""
    sample_text = (
        "Operating systems manage hardware resources. Process scheduling determines which process gets CPU time. "
        "Memory management involves virtual memory and paging. File systems provide structured access to persistent storage. "
    ) * 10  # ~1100 characters

    pages = [
        {"page_number": 1, "text": sample_text},
        {"page_number": 2, "text": "Short conclusion page for operating systems."}
    ]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.create_chunks(pages, notebook_id="cs-101", filename="os_notes.txt")

    assert len(chunks) >= 2, f"Expected multiple chunks, got {len(chunks)}"
    for chunk in chunks:
        assert len(chunk["text"]) <= 550, f"Chunk exceeded expected size: {len(chunk['text'])}"
        assert chunk["metadata"]["notebook_id"] == "cs-101"
        assert chunk["metadata"]["filename"] == "os_notes.txt"
        assert "page_number" in chunk["metadata"]
        assert "chunk_id" in chunk

    print(f" RecursiveCharacterTextSplitter test PASSED ({len(chunks)} chunks created)")


def test_embedding_service():
    """Verify 768-dimensional embedding generation."""
    service = EmbeddingService()
    test_text = "What is the three-way handshake in TCP?"

    vector = service.get_embedding(test_text)
    assert len(vector) == EMBEDDING_DIMENSION, f"Expected {EMBEDDING_DIMENSION} dimensions, got {len(vector)}"

    batch_vectors = service.get_embeddings_batch([test_text, "Explain UDP protocol."])
    assert len(batch_vectors) == 2
    assert len(batch_vectors[0]) == EMBEDDING_DIMENSION
    assert len(batch_vectors[1]) == EMBEDDING_DIMENSION

    print(f" EmbeddingService test PASSED (768-dim vectors verified, configured={service.is_configured})")


if __name__ == "__main__":
    print("Running Ingestion & Embedding Pipeline Tests...")
    test_txt_parser()
    test_text_splitter()
    test_embedding_service()
    print(" All ingestion and embedding pipeline components passed successfully!")

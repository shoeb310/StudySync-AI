"""
Verification test script for streaming RAG and citation retrieval:
- Ingests test document with TCP networking concepts
- Queries /api/v1/chat/stream with SSE consumer
- Verifies token-by-token streaming response
- Verifies citation metadata payload [Doc 1, Page 1]
- Verifies stream termination with [DONE]
- Cleans up test notebook
"""
import io
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_streaming_rag_with_citations():
    """Verify end-to-end RAG retrieval, Gemini streaming, and citation delivery."""
    test_notebook_id = "test-rag-networking"
    test_filename = "tcp_protocol_guide.txt"
    sample_study_material = (
        "The Transmission Control Protocol (TCP) uses a three-way handshake "
        "(SYN, SYN-ACK, ACK) to establish a reliable connection between client and server. "
        "During this handshake, both endpoints agree upon initial sequence numbers and socket buffers. "
        "Unlike UDP, TCP guarantees delivery, error checking, and packet ordering."
    )

    # 1. Ingest test material
    upload_file = {
        "file": (test_filename, io.BytesIO(sample_study_material.encode("utf-8")), "text/plain")
    }
    upload_res = client.post("/api/v1/upload", data={"notebook_id": test_notebook_id}, files=upload_file)
    assert upload_res.status_code == 201, f"Setup upload failed: {upload_res.text}"
    print(f" Test document ingested into '{test_notebook_id}'")

    # 2. Test POST /api/v1/chat/stream
    query_payload = {
        "query": "How does TCP establish a connection?",
        "notebook_id": test_notebook_id
    }

    tokens_received = []
    citations_received = []
    received_done = False

    with client.stream("POST", "/api/v1/chat/stream", json=query_payload) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        for line in response.iter_lines():
            line_str = line if isinstance(line, str) else line.decode("utf-8")
            line_str = line_str.strip()

            if not line_str.startswith("data:"):
                continue

            data_str = line_str[len("data:"):].strip()

            if data_str == "[DONE]":
                received_done = True
                break

            try:
                event = json.loads(data_str)
                if event.get("type") == "content":
                    tokens_received.append(event.get("token", ""))
                elif event.get("type") == "citations":
                    citations_received = event.get("citations", [])
            except json.JSONDecodeError:
                continue

    full_answer = "".join(tokens_received)
    print("\n--- Streaming Response ---")
    print(full_answer.strip())
    print("--------------------------")

    # Assertions
    assert len(tokens_received) > 0, "No content tokens received in stream."
    assert received_done, "Stream did not terminate with [DONE]."
    assert len(citations_received) > 0, "No citation metadata received."

    first_citation = citations_received[0]
    assert first_citation["filename"] == test_filename
    assert first_citation["page_number"] == 1
    assert "three-way handshake" in first_citation["snippet"].lower()

    print(f" Streaming RAG test PASSED ({len(tokens_received)} token chunks, {len(citations_received)} citations)")
    print(f"   - Citation: [Doc {first_citation['doc_id']}, Page {first_citation['page_number']}] -> {first_citation['filename']}")

    # 3. Cleanup test notebook
    del_res = client.delete(f"/api/v1/documents/{test_notebook_id}")
    assert del_res.status_code == 200
    print(f" Cleaned up test notebook '{test_notebook_id}'")


def test_empty_notebook_query():
    """Verify handling when querying a notebook with no indexed documents."""
    query_payload = {
        "query": "What is quantum computing?",
        "notebook_id": "non-existent-notebook"
    }

    tokens = []
    with client.stream("POST", "/api/v1/chat/stream", json=query_payload) as response:
        for line in response.iter_lines():
            line_str = line if isinstance(line, str) else line.decode("utf-8")
            if line_str.startswith("data:"):
                data_str = line_str[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    if event.get("type") == "content":
                        tokens.append(event.get("token", ""))
                except Exception:
                    pass

    answer = "".join(tokens)
    assert "couldn't find" in answer.lower() or "upload" in answer.lower()
    print(" Empty notebook query test PASSED (graceful notice returned)")


if __name__ == "__main__":
    print("Running Streaming RAG & Citation Retrieval Tests...")
    test_streaming_rag_with_citations()
    test_empty_notebook_query()
    print(" All streaming retrieval verification tests passed successfully!")

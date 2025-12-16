"""
Verification test script for ingestion and notebook management endpoints:
- POST /api/v1/upload (multipart document upload, chunking & ChromaDB upsert)
- GET /api/v1/notebooks (notebook discovery and summary)
- DELETE /api/v1/documents/{notebook_id} (notebook vector pruning)
"""
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_document_upload_and_lifecycle():
    """Verify full document upload, notebook aggregation, and deletion lifecycle."""
    test_notebook_id = "test-cs-101"
    test_filename = "operating_systems_summary.txt"
    sample_content = (
        "Operating systems coordinate CPU scheduling, physical memory, and storage devices. "
        "A process is an instance of a computer program that is being executed by one or many threads. "
        "Virtual memory maps virtual addresses used by an application into physical addresses in computer memory. "
    ) * 8  # ~1100 characters, creates ~3 chunks

    # 1. Test POST /api/v1/upload
    file_payload = {
        "file": (test_filename, io.BytesIO(sample_content.encode("utf-8")), "text/plain")
    }
    data_payload = {
        "notebook_id": test_notebook_id
    }

    upload_res = client.post("/api/v1/upload", data=data_payload, files=file_payload)
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    assert upload_data["notebook_id"] == test_notebook_id
    assert upload_data["filename"] == test_filename
    assert upload_data["chunks_ingested"] >= 2
    print(f" POST /api/v1/upload test PASSED ({upload_data['chunks_ingested']} chunks ingested)")

    # 2. Test GET /api/v1/notebooks
    list_res = client.get("/api/v1/notebooks")
    assert list_res.status_code == 200, f"List failed: {list_res.text}"
    notebooks = list_res.json().get("notebooks", [])
    matching = [nb for nb in notebooks if nb["notebook_id"] == test_notebook_id]
    assert len(matching) == 1, f"Notebook '{test_notebook_id}' not found in active notebooks."
    assert matching[0]["document_count"] >= 1
    assert test_filename in matching[0]["documents"]
    print(f" GET /api/v1/notebooks test PASSED (found notebook with {matching[0]['document_count']} docs)")

    # 3. Test DELETE /api/v1/documents/{notebook_id}
    delete_res = client.delete(f"/api/v1/documents/{test_notebook_id}")
    assert delete_res.status_code == 200, f"Delete failed: {delete_res.text}"
    delete_data = delete_res.json()
    assert delete_data["status"] == "success"
    assert delete_data["deleted_chunks"] >= 2
    print(f" DELETE /api/v1/documents/{test_notebook_id} test PASSED ({delete_data['deleted_chunks']} chunks deleted)")

    # 4. Verify notebook is now cleared
    list_after = client.get("/api/v1/notebooks").json().get("notebooks", [])
    matching_after = [nb for nb in list_after if nb["notebook_id"] == test_notebook_id]
    assert len(matching_after) == 0
    print(" Verified notebook list reflects document deletion")


def test_invalid_upload_handling():
    """Verify validation on malformed uploads."""
    # Test unsupported extension
    bad_file = {"file": ("report.docx", io.BytesIO(b"dummy data"), "application/octet-stream")}
    res = client.post("/api/v1/upload", data={"notebook_id": "math-201"}, files=bad_file)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]

    # Test empty notebook ID
    good_file = {"file": ("notes.txt", io.BytesIO(b"Valid content"), "text/plain")}
    res2 = client.post("/api/v1/upload", data={"notebook_id": "   "}, files=good_file)
    assert res2.status_code == 400
    assert "Notebook ID cannot be empty" in res2.json()["detail"]

    print(" Invalid upload validation tests PASSED")


if __name__ == "__main__":
    print("Running Ingestion & Notebook Management Endpoint Tests...")
    test_document_upload_and_lifecycle()
    test_invalid_upload_handling()
    print(" All endpoint verification tests passed successfully!")

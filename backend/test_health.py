"""
Verification test: Healthcheck and Application Skeleton
Runs against FastAPI app using FastAPI TestClient.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "StudySync" in data["service"]
    print(" Root endpoint test PASSED")


def test_health_endpoint():
    """Verify that /api/v1/health returns system and dependency status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "chromadb" in data
    assert "ai_configured" in data
    print(" Health endpoint test PASSED")
    print(f"   - Status: {data['status']}")
    print(f"   - ChromaDB: {data['chromadb']}")
    print(f"   - AI Configured: {data['ai_configured']}")


if __name__ == "__main__":
    print("Running Healthcheck Verification Tests...")
    test_root_endpoint()
    test_health_endpoint()
    print("All healthcheck verification tests passed successfully!")

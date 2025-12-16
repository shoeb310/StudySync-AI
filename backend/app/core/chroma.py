import logging
import os
from typing import Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client: Optional[Any] = None


def get_chroma_client():
    """
    Retrieve or initialize the ChromaDB client.
    Attempts HTTP client connection (for Docker Compose network).
    Falls back gracefully to local PersistentClient if HTTP server is not accessible.
    """
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    # Attempt 1: Connect to HTTP server (Docker or remote instance)
    try:
        logger.info(f"Connecting to ChromaDB HTTP at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(allow_reset=False, anonymized_telemetry=False)
        )
        # Test connection
        client.heartbeat()
        _chroma_client = client
        logger.info("Successfully connected to ChromaDB HTTP server.")
        return _chroma_client
    except Exception as http_err:
        logger.warning(
            f"ChromaDB HTTP server unavailable at {settings.CHROMA_HOST}:{settings.CHROMA_PORT} ({http_err}). "
            f"Falling back to local persistent client at './chroma_data'."
        )

    # Attempt 2: Fallback to local persistent storage (ideal for local testing without Docker)
    try:
        persist_dir = os.path.join(os.getcwd(), "chroma_data")
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False)
        )
        logger.info(f"Initialized local ChromaDB PersistentClient at '{persist_dir}'.")
        return _chroma_client
    except Exception as fallback_err:
        logger.error(f"Failed to initialize ChromaDB local client: {fallback_err}")
        raise fallback_err


def get_documents_collection():
    """
    Retrieve or create the main StudySync documents collection.
    Metadata filter strategy: notebook_id stored on every chunk.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def check_chroma_health() -> Dict[str, Any]:
    """
    Ping ChromaDB to verify availability.
    Returns status dict suitable for healthcheck responses.
    """
    try:
        client = get_chroma_client()
        heartbeat = client.heartbeat()
        version = client.get_version()
        client_type = "http" if isinstance(client, chromadb.HttpClient) else "persistent"
        return {
            "status": "connected",
            "type": client_type,
            "heartbeat": heartbeat,
            "version": version,
            "host": f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
        }
    except Exception as exc:
        logger.warning(f"ChromaDB healthcheck failed: {exc}")
        return {
            "status": "disconnected",
            "error": str(exc),
            "host": f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
        }

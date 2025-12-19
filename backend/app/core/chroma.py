import logging
import os
from typing import Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client: Optional[Any] = None


import urllib.request
import json

def _is_chroma_server(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quickly probe if a true ChromaDB HTTP server is responding on host:port."""
    for path in ("/api/v1/heartbeat", "/api/v2/heartbeat"):
        try:
            url = f"http://{host}:{port}{path}"
            req = urllib.request.Request(url, headers={"User-Agent": "StudySync-Chroma-Probe"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    if "nanosecond heartbeat" in data:
                        return True
        except Exception:
            continue
    return False


def get_chroma_client():
    """
    Retrieve or initialize the ChromaDB client.
    Attempts HTTP client connection (for Docker Compose network).
    Falls back gracefully to local PersistentClient if HTTP server is not accessible.
    """
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    # Attempt 1: Connect to HTTP server (Docker or remote instance) if genuinely available
    if _is_chroma_server(settings.CHROMA_HOST, settings.CHROMA_PORT, timeout=0.8):
        try:
            logger.info(f"Connecting to ChromaDB HTTP at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(allow_reset=False, anonymized_telemetry=False)
            )
            client.heartbeat()
            _chroma_client = client
            logger.info("Successfully connected to ChromaDB HTTP server.")
            return _chroma_client
        except Exception as http_err:
            logger.warning(
                f"ChromaDB HTTP connection failed at {settings.CHROMA_HOST}:{settings.CHROMA_PORT} ({http_err}). "
                f"Falling back to local persistent client."
            )
    else:
        logger.info(
            f"No ChromaDB HTTP server detected at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}. "
            f"Using local PersistentClient at './chroma_data'."
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
        client_type = "http" if "http" in type(client).__name__.lower() else "persistent"
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

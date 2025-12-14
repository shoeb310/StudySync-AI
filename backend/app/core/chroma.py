import logging
from typing import Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client: Optional[chromadb.HttpClient] = None


def get_chroma_client() -> chromadb.HttpClient:
    """
    Retrieve or initialize the singleton ChromaDB HTTP client.
    Connects to the external Chroma container or local instance.
    """
    global _chroma_client
    if _chroma_client is None:
        logger.info(f"Connecting to ChromaDB at http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
        try:
            _chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(allow_reset=False, anonymized_telemetry=False)
            )
            logger.info("Successfully initialized ChromaDB HttpClient.")
        except Exception as exc:
            logger.error(f"Failed to initialize ChromaDB HttpClient: {exc}")
            raise exc

    return _chroma_client


def get_documents_collection():
    """
    Retrieve or create the main StudySync documents collection.
    Metadata filter strategy: notebook_id will be stored on every chunk.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def check_chroma_health() -> Dict[str, Any]:
    """
    Ping ChromaDB heartbeat to verify availability.
    Returns status dict suitable for healthcheck responses.
    """
    try:
        client = get_chroma_client()
        heartbeat = client.heartbeat()
        version = client.get_version()
        return {
            "status": "connected",
            "heartbeat": heartbeat,
            "version": version,
            "host": f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
        }
    except Exception as exc:
        logger.warning(f"ChromaDB healthcheck check failed: {exc}")
        return {
            "status": "disconnected",
            "error": str(exc),
            "host": f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
        }

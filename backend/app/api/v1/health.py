from datetime import datetime, timezone
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

from app.core.config import settings
from app.core.chroma import check_chroma_health

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    chromadb: Dict[str, Any]
    ai_configured: bool


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health & Dependency Status",
    description="Returns operational status of FastAPI backend, ChromaDB vector database connectivity, and Gemini API readiness."
)
async def get_health():
    """
    Perform a complete healthcheck across backend dependencies.
    """
    chroma_status = check_chroma_health()
    gemini_ready = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    is_healthy = (chroma_status.get("status") == "connected")

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        chromadb=chroma_status,
        ai_configured=gemini_ready
    )

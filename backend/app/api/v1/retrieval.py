import logging
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream RAG Chat with Citations",
    description="Streams token-by-token answers from Gemini grounded in notebook context, ending with citation metadata via Server-Sent Events (SSE)."
)
async def chat_stream(payload: ChatRequest):
    """
    Server-Sent Events endpoint streaming answer tokens followed by citation sources.
    """
    logger.info(f"Initiating chat stream for query in notebook '{payload.notebook_id}'...")

    return StreamingResponse(
        rag_service.stream_chat(
            query=payload.query,
            notebook_id=payload.notebook_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8"
        }
    )

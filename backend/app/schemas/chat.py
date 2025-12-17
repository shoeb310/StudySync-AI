from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for initiating a streaming academic chat query."""
    query: str = Field(..., min_length=1, description="Student's study question")
    notebook_id: str = Field(..., min_length=1, description="Active study notebook to query")


class CitationSource(BaseModel):
    """Metadata detailing the source chunk for a citation tag."""
    doc_id: int = Field(..., description="1-indexed document citation number matching [Doc X, Page Y]")
    chunk_id: str = Field(..., description="Unique chunk identifier in vector database")
    filename: str = Field(..., description="Source document filename")
    page_number: int = Field(..., description="Page number where the source text appears")
    snippet: str = Field(..., description="Extracted text chunk snippet")


class ChatEvent(BaseModel):
    """Data frame for Server-Sent Events (SSE)."""
    type: str = Field(..., description="'content', 'citations', or 'error'")
    token: Optional[str] = None
    citations: Optional[List[CitationSource]] = None
    error: Optional[str] = None

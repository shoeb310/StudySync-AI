from typing import List
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response returned upon successful document upload and chunking."""
    status: str = Field(default="success", description="Status of ingestion")
    notebook_id: str = Field(..., description="Target notebook identifier")
    filename: str = Field(..., description="Uploaded file name")
    chunks_ingested: int = Field(..., description="Number of text chunks embedded and saved")
    total_characters: int = Field(..., description="Total character count across all chunks")


class NotebookSummary(BaseModel):
    """Summary of a study notebook and its contained documents."""
    notebook_id: str = Field(..., description="Unique notebook identifier")
    document_count: int = Field(..., description="Number of distinct uploaded documents")
    chunk_count: int = Field(..., description="Total indexed text chunks")
    documents: List[str] = Field(default_factory=list, description="List of document filenames")


class NotebookListResponse(BaseModel):
    """List of active notebooks across the system."""
    notebooks: List[NotebookSummary] = Field(default_factory=list)


class DeleteResponse(BaseModel):
    """Response returned when clearing documents from a notebook."""
    status: str = Field(default="success")
    notebook_id: str
    message: str
    deleted_chunks: int = 0

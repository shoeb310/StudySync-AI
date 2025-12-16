import logging
from collections import defaultdict
from fastapi import APIRouter, HTTPException, status
from app.core.chroma import get_documents_collection
from app.schemas.document import NotebookListResponse, NotebookSummary, DeleteResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/notebooks",
    response_model=NotebookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Active Notebooks",
    description="Scans indexed documents and returns all active notebooks with their document and chunk counts."
)
async def list_notebooks():
    """
    Aggregate all active study notebooks and document counts from vector metadata.
    """
    try:
        collection = get_documents_collection()
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", []) or []

        notebook_map = defaultdict(lambda: {"documents": set(), "chunks": 0})

        for meta in metadatas:
            if not meta:
                continue
            nb_id = meta.get("notebook_id")
            filename = meta.get("filename")

            if nb_id:
                notebook_map[nb_id]["chunks"] += 1
                if filename:
                    notebook_map[nb_id]["documents"].add(filename)

        notebook_list = [
            NotebookSummary(
                notebook_id=nb_id,
                document_count=len(info["documents"]),
                chunk_count=info["chunks"],
                documents=sorted(list(info["documents"]))
            )
            for nb_id, info in sorted(notebook_map.items())
        ]

        return NotebookListResponse(notebooks=notebook_list)

    except Exception as exc:
        logger.error(f"Failed to list notebooks: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve notebook summaries: {str(exc)}"
        )


@router.delete(
    "/documents/{notebook_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear Notebook Documents",
    description="Deletes all indexed vectors and text chunks associated with the specified notebook ID."
)
async def clear_notebook_documents(notebook_id: str):
    """
    Delete all vector records for a specific notebook.
    """
    sanitized_id = notebook_id.strip()
    if not sanitized_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook ID cannot be empty."
        )

    try:
        collection = get_documents_collection()

        # Check existing items before deletion
        existing = collection.get(
            where={"notebook_id": sanitized_id},
            include=["metadatas"]
        )
        count = len(existing.get("ids", []))

        if count == 0:
            return DeleteResponse(
                status="success",
                notebook_id=sanitized_id,
                message=f"No documents found for notebook '{sanitized_id}'.",
                deleted_chunks=0
            )

        collection.delete(where={"notebook_id": sanitized_id})
        logger.info(f"Deleted {count} vector chunks for notebook '{sanitized_id}'.")

        return DeleteResponse(
            status="success",
            notebook_id=sanitized_id,
            message=f"Successfully purged {count} chunks for notebook '{sanitized_id}'.",
            deleted_chunks=count
        )

    except Exception as exc:
        logger.error(f"Failed to delete documents for notebook '{sanitized_id}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notebook documents: {str(exc)}"
        )

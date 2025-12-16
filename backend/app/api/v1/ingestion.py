import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.core.chroma import get_documents_collection
from app.services.document_parser import DocumentParser, DocumentParserError
from app.services.text_splitter import RecursiveCharacterTextSplitter
from app.services.embedding_service import embedding_service
from app.schemas.document import UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Ingest Document",
    description="Uploads a PDF or TXT document, extracts text, chunks it into 500-char windows, generates embeddings, and indexes into ChromaDB."
)
async def upload_document(
    notebook_id: str = Form(..., description="Identifier of the target notebook (e.g., cs-101)"),
    file: UploadFile = File(..., description="Document file (.pdf or .txt)")
):
    # Validate notebook_id
    sanitized_notebook_id = notebook_id.strip()
    if not sanitized_notebook_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook ID cannot be empty."
        )

    # Validate file extension
    filename = file.filename or "uploaded_document"
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{extension}'. Only .pdf and .txt files are supported."
        )

    # Read binary content
    try:
        content = await file.read()
    except Exception as read_err:
        logger.error(f"Failed to read upload stream for '{filename}': {read_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # 1. Parse document into pages
    try:
        pages = DocumentParser.parse_document(content, filename)
    except DocumentParserError as parse_err:
        logger.warning(f"Parsing error for '{filename}': {parse_err}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(parse_err)
        )

    if not pages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text could be extracted from this document."
        )

    # 2. Split pages into 500-char chunks with 50-char overlap
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.create_chunks(pages, notebook_id=sanitized_notebook_id, filename=filename)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document text was too short or empty after processing."
        )

    # 3. Generate 768-dim embeddings for all chunk texts
    chunk_texts = [c["text"] for c in chunks]
    try:
        embeddings = embedding_service.get_embeddings_batch(chunk_texts)
    except Exception as emb_err:
        logger.error(f"Failed to generate embeddings for '{filename}': {emb_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute vector embeddings: {str(emb_err)}"
        )

    # 4. Upsert vectors and metadata into ChromaDB
    try:
        collection = get_documents_collection()
        chunk_ids = [c["chunk_id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunk_texts
        )
        logger.info(f"Successfully upserted {len(chunks)} chunks into ChromaDB for '{filename}'.")
    except Exception as db_err:
        logger.error(f"ChromaDB upsert failed for '{filename}': {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database indexing failed: {str(db_err)}"
        )

    total_chars = sum(len(t) for t in chunk_texts)

    return UploadResponse(
        status="success",
        notebook_id=sanitized_notebook_id,
        filename=filename,
        chunks_ingested=len(chunks),
        total_characters=total_chars
    )

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.chroma import check_chroma_health, get_documents_collection
from app.api.v1.router import api_v1_router

# Configure clean, human-readable logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)
logger = logging.getLogger("studysync.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs on startup and shutdown to initialize resources.
    """
    logger.info("==================================================")
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("==================================================")

    # Validate ChromaDB connectivity on startup
    chroma_check = check_chroma_health()
    if chroma_check.get("status") == "connected":
        logger.info(f"Connected to ChromaDB at {chroma_check.get('host')} (v{chroma_check.get('version')})")
        try:
            collection = get_documents_collection()
            logger.info(f"ChromaDB collection initialized: '{collection.name}'")
        except Exception as e:
            logger.warning(f"Could not load ChromaDB collection: {e}")
    else:
        logger.warning(f"ChromaDB not reachable at startup ({chroma_check.get('error')}). Endpoints will retry on request.")

    # Check Gemini API Key presence
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        logger.info("Gemini API key is configured.")
    else:
        logger.warning("GEMINI_API_KEY is not set or empty. Embedding and Chat features will require it.")

    yield

    logger.info("Shutting down StudySync AI backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI service for StudySync AI - Academic RAG with ChromaDB & Gemini 1.5 Flash.",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """Root landing endpoint with service metadata and documentation links."""
    return JSONResponse({
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    })

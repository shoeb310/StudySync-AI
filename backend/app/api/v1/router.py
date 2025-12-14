from fastapi import APIRouter
from app.api.v1 import health

api_v1_router = APIRouter()

# Core system health & dependency checks
api_v1_router.include_router(health.router, tags=["System Health"])

# Day 2 & 3: Ingestion & Notebook Management will be mounted here:
# api_v1_router.include_router(ingestion.router, prefix="/upload", tags=["Document Ingestion"])
# api_v1_router.include_router(notebooks.router, tags=["Notebook Management"])

# Day 4: Streaming RAG & Retrieval will be mounted here:
# api_v1_router.include_router(retrieval.router, prefix="/chat", tags=["Streaming Retrieval"])

from fastapi import APIRouter
from app.api.v1 import health, ingestion, notebooks, retrieval

api_v1_router = APIRouter()

# Core system health & dependency checks
api_v1_router.include_router(health.router, tags=["System Health"])

# Document ingestion and notebook management routers
api_v1_router.include_router(ingestion.router, prefix="/upload", tags=["Document Ingestion"])
api_v1_router.include_router(notebooks.router, tags=["Notebook Management"])

# Streaming retrieval and chat routers
api_v1_router.include_router(retrieval.router, prefix="/chat", tags=["Streaming Retrieval"])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.models import router as models_router
from app.api.prediction import router as prediction_router
from app.api.routes import router
from app.api.temporal import router as temporal_router
from app.config import get_settings

settings = get_settings()
app = FastAPI(
    title="MykoKnoks API",
    version=settings.app_version,
    description="Nordic ecological intelligence: fungal habitat and fruiting forecast engine",
    root_path=settings.root_path,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)
app.include_router(temporal_router, prefix=settings.api_prefix)
app.include_router(prediction_router, prefix=settings.api_prefix)
app.include_router(models_router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "root_path": settings.root_path,
    }

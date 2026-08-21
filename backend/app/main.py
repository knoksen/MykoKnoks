from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings

settings = get_settings()
app = FastAPI(title="MykoKnoks API", version="0.1.0", description="Nordic fungal habitat and fruiting forecast engine")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}

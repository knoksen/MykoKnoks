from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.model_registry import get_model, list_models

router = APIRouter()


@router.get("/models")
def models() -> list[dict]:
    return list_models()


@router.get("/models/{model_id}")
def model(model_id: str) -> dict:
    descriptor = get_model(model_id)
    if descriptor is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return descriptor

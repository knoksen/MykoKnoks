from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ModelDescriptor:
    id: str
    name: str
    version: str
    status: str
    species: tuple[str, ...]
    model_type: str
    calibrated: bool
    trained: bool
    feature_contract: tuple[str, ...]
    validation: str
    semantics: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["species"] = list(self.species)
        payload["feature_contract"] = list(self.feature_contract)
        return payload


_BUILTIN_MODELS = (
    ModelDescriptor(
        id="semilanceata-gis-heuristic-v1",
        name="Semilanceata ecological GIS heuristic",
        version="1.0.0",
        status="production-heuristic",
        species=("Psilocybe semilanceata",),
        model_type="explainable weighted ecological index",
        calibrated=False,
        trained=False,
        feature_contract=(
            "open_land_score",
            "substrate_moisture_score",
            "forest_score",
            "forest_edge_proxy",
            "elevation_m",
            "slope_deg",
            "terrain_roughness_m",
        ),
        validation="unit-tested feature semantics; no national spatial calibration yet",
        semantics="Suitability index. Not occurrence probability or identification advice.",
    ),
    ModelDescriptor(
        id="fungal-sdm-spatial-cv-v1-candidate",
        name="Spatial cross-validation SDM candidate",
        version="1.0.0",
        status="training-pipeline",
        species=(),
        model_type="HistGradientBoostingClassifier with grouped spatial CV",
        calibrated=False,
        trained=False,
        feature_contract=(
            "open_land_score",
            "wetland_score",
            "forest_score",
            "substrate_moisture_score",
            "elevation_m",
            "slope_deg",
            "terrain_roughness_m",
            "antecedent_precip_24h_mm",
            "antecedent_precip_72h_mm",
            "moisture_memory_index",
        ),
        validation="requires occurrence/background dataset and held-out spatial blocks",
        semantics="Candidate training contract only until a manifest with CV metrics is registered.",
    ),
)


def list_models() -> list[dict[str, Any]]:
    return [model.as_dict() for model in _BUILTIN_MODELS]


def get_model(model_id: str) -> dict[str, Any] | None:
    for model in _BUILTIN_MODELS:
        if model.id == model_id:
            return model.as_dict()
    return None

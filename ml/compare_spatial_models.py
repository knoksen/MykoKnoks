"""Compare habitat SDM candidates under identical grouped spatial folds.

This benchmark deliberately evaluates discrimination and probability-score quality without
claiming calibration. Presence-only records are compared against sampled background, not
confirmed biological absences.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from features import TARGET_COLUMN, V1_HABITAT_FEATURE_COLUMNS

RANDOM_STATE = 42


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _group_signature(values: pd.Series) -> str:
    payload = "\n".join(sorted(set(values.astype(str))))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _logistic() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _random_forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=14,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


def _gradient_boosting() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=24,
        l2_regularization=0.8,
        random_state=RANDOM_STATE,
    )


MODEL_FACTORIES: dict[str, Callable[[], Any]] = {
    "logistic_regression": _logistic,
    "random_forest": _random_forest,
    "hist_gradient_boosting": _gradient_boosting,
}


def _safe_roc_auc(y_true: pd.Series, probabilities) -> float | None:
    if y_true.nunique() < 2:
        return None
    return float(roc_auc_score(y_true, probabilities))


def _safe_average_precision(y_true: pd.Series, probabilities) -> float | None:
    if int(y_true.sum()) == 0:
        return None
    return float(average_precision_score(y_true, probabilities))


def _round(value: float | None) -> float | None:
    return None if value is None or not math.isfinite(value) else round(float(value), 6)


def _summary(values: list[float | None]) -> dict[str, float | None]:
    valid = [float(value) for value in values if value is not None and math.isfinite(value)]
    if not valid:
        return {"mean": None, "variance": None, "min": None, "max": None}
    return {
        "mean": _round(statistics.fmean(valid)),
        "variance": _round(statistics.pvariance(valid)) if len(valid) > 1 else 0.0,
        "min": _round(min(valid)),
        "max": _round(max(valid)),
    }


def _evaluate_model(
    *,
    name: str,
    factory: Callable[[], Any],
    frame: pd.DataFrame,
    folds: list[tuple[Any, Any]],
    group_column: str,
) -> dict[str, Any]:
    metrics: list[dict[str, Any]] = []
    features = V1_HABITAT_FEATURE_COLUMNS

    for fold_number, (train_idx, test_idx) in enumerate(folds, start=1):
        train = frame.iloc[train_idx]
        test = frame.iloc[test_idx]
        model = factory()
        model.fit(train[features], train[TARGET_COLUMN])
        probabilities = model.predict_proba(test[features])[:, 1]

        roc_auc = _safe_roc_auc(test[TARGET_COLUMN], probabilities)
        average_precision = _safe_average_precision(test[TARGET_COLUMN], probabilities)
        brier = float(brier_score_loss(test[TARGET_COLUMN], probabilities))
        loss = float(log_loss(test[TARGET_COLUMN], probabilities, labels=[0, 1]))

        metrics.append(
            {
                "fold": fold_number,
                "train_rows": len(train),
                "test_rows": len(test),
                "train_groups": int(train[group_column].nunique()),
                "test_groups": int(test[group_column].nunique()),
                "test_group_sha256": _group_signature(test[group_column]),
                "test_presence_rows": int(test[TARGET_COLUMN].sum()),
                "test_background_rows": int(len(test) - test[TARGET_COLUMN].sum()),
                "roc_auc": _round(roc_auc),
                "pr_auc": _round(average_precision),
                "brier_score": _round(brier),
                "log_loss": _round(loss),
            }
        )

    return {
        "model_key": name,
        "fold_metrics": metrics,
        "summary": {
            "roc_auc": _summary([row["roc_auc"] for row in metrics]),
            "pr_auc": _summary([row["pr_auc"] for row in metrics]),
            "brier_score": _summary([row["brier_score"] for row in metrics]),
            "log_loss": _summary([row["log_loss"] for row in metrics]),
        },
    }


def _ranking_key(result: dict[str, Any]) -> tuple[float, float, float, float]:
    summary = result["summary"]
    pr_auc = summary["pr_auc"]["mean"]
    roc_auc = summary["roc_auc"]["mean"]
    brier = summary["brier_score"]["mean"]
    loss = summary["log_loss"]["mean"]
    return (
        -1.0 if pr_auc is None else float(pr_auc),
        -1.0 if roc_auc is None else float(roc_auc),
        -(float(brier) if brier is not None else 1e9),
        -(float(loss) if loss is not None else 1e9),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--species", required=True)
    parser.add_argument("--group-column", default="spatial_block")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, default=Path("models/comparison"))
    args = parser.parse_args()

    required = [*V1_HABITAT_FEATURE_COLUMNS, TARGET_COLUMN, args.group_column]
    frame = pd.read_csv(args.csv).dropna(subset=required).copy()
    if frame.empty:
        raise SystemExit("No complete rows remain after applying the v1 habitat feature contract.")
    if frame[TARGET_COLUMN].nunique() < 2:
        raise SystemExit("Benchmark requires presence and sampled-background rows.")

    groups = frame[args.group_column].astype(str)
    unique_groups = int(groups.nunique())
    n_splits = min(max(2, args.folds), unique_groups)
    if n_splits < 2:
        raise SystemExit("Spatial model comparison requires at least two spatial groups.")

    splitter = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    # Materialize once: every candidate is evaluated on exactly the same train/test partitions.
    folds = list(splitter.split(frame[V1_HABITAT_FEATURE_COLUMNS], frame[TARGET_COLUMN], groups))

    results = [
        _evaluate_model(
            name=name,
            factory=factory,
            frame=frame,
            folds=folds,
            group_column=args.group_column,
        )
        for name, factory in MODEL_FACTORIES.items()
    ]
    ranked = sorted(results, key=_ranking_key, reverse=True)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.species.strip().casefold().replace(" ", "-").replace("/", "-")
    artifacts: dict[str, str] = {}
    for name, factory in MODEL_FACTORIES.items():
        model = factory()
        model.fit(frame[V1_HABITAT_FEATURE_COLUMNS], frame[TARGET_COLUMN])
        path = args.out_dir / f"{slug}-{name}-v1.1.joblib"
        joblib.dump(
            {
                "model": model,
                "features": V1_HABITAT_FEATURE_COLUMNS,
                "species": args.species,
                "model_key": name,
                "calibrated": False,
            },
            path,
        )
        artifacts[name] = str(path)

    report = {
        "schema_version": "mykoknoks-model-comparison-v1",
        "species": args.species,
        "created_at": datetime.now(UTC).isoformat(),
        "random_state": RANDOM_STATE,
        "trained": True,
        "calibrated": False,
        "probability_claim_allowed": False,
        "target_semantics": "presence versus sampled background, not confirmed biological absence",
        "feature_contract": V1_HABITAT_FEATURE_COLUMNS,
        "dataset": {
            "path": str(args.csv),
            "sha256": _sha256(args.csv),
            "rows": len(frame),
            "presence_rows": int(frame[TARGET_COLUMN].sum()),
            "background_rows": int(len(frame) - frame[TARGET_COLUMN].sum()),
            "spatial_groups": unique_groups,
            "group_column": args.group_column,
        },
        "cross_validation": {
            "method": "StratifiedGroupKFold",
            "folds": n_splits,
            "same_partitions_for_all_models": True,
        },
        "selection": {
            "ranking_rule": "PR-AUC desc, ROC-AUC desc, Brier asc, log-loss asc",
            "best_candidate": ranked[0]["model_key"],
            "promotion_status": "benchmark-only",
        },
        "models": results,
        "artifacts": artifacts,
        "scientific_guardrail": (
            "These scores compare presence records with sampled background. They are not calibrated "
            "occurrence probabilities. Independent spatial validation and an explicit calibration "
            "gate are required before probability language is allowed."
        ),
    }

    report_path = args.out_dir / f"{slug}-model-comparison-v1.1.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"report={report_path.resolve()}")


if __name__ == "__main__":
    main()

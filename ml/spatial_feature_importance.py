"""Estimate model-agnostic habitat feature importance on spatial holdout folds."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedGroupKFold

from compare_spatial_models import MODEL_FACTORIES, RANDOM_STATE
from features import TARGET_COLUMN, V1_HABITAT_FEATURE_COLUMNS


def _round(value: float | None) -> float | None:
    return None if value is None or not math.isfinite(value) else round(float(value), 6)


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "mean": _round(float(statistics.fmean(values))) or 0.0,
        "variance": _round(float(statistics.pvariance(values))) if len(values) > 1 else 0.0,
        "min": _round(min(values)) or 0.0,
        "max": _round(max(values)) or 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--species", required=True)
    parser.add_argument("--model", choices=sorted(MODEL_FACTORIES), default="logistic_regression")
    parser.add_argument("--group-column", default="spatial_block")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path("models/feature-importance.json"))
    args = parser.parse_args()

    required = [*V1_HABITAT_FEATURE_COLUMNS, TARGET_COLUMN, args.group_column]
    frame = pd.read_csv(args.csv).dropna(subset=required).copy()
    if frame.empty or frame[TARGET_COLUMN].nunique() < 2:
        raise SystemExit("Feature importance requires complete presence and background rows.")

    groups = frame[args.group_column].astype(str)
    n_splits = min(max(2, args.folds), int(groups.nunique()))
    splitter = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    partitions = list(
        splitter.split(frame[V1_HABITAT_FEATURE_COLUMNS], frame[TARGET_COLUMN], groups)
    )

    by_feature: dict[str, list[float]] = {name: [] for name in V1_HABITAT_FEATURE_COLUMNS}
    fold_results: list[dict[str, Any]] = []
    factory = MODEL_FACTORIES[args.model]

    for fold_number, (train_idx, test_idx) in enumerate(partitions, start=1):
        train = frame.iloc[train_idx]
        test = frame.iloc[test_idx]
        if test[TARGET_COLUMN].nunique() < 2:
            continue

        model = factory()
        model.fit(train[V1_HABITAT_FEATURE_COLUMNS], train[TARGET_COLUMN])
        result = permutation_importance(
            model,
            test[V1_HABITAT_FEATURE_COLUMNS],
            test[TARGET_COLUMN],
            scoring="average_precision",
            n_repeats=max(2, args.repeats),
            random_state=RANDOM_STATE + fold_number,
            n_jobs=-1,
        )

        fold_importances = {}
        for feature, value in zip(V1_HABITAT_FEATURE_COLUMNS, result.importances_mean, strict=True):
            importance = float(value)
            by_feature[feature].append(importance)
            fold_importances[feature] = _round(importance)
        fold_results.append(
            {
                "fold": fold_number,
                "train_rows": len(train),
                "test_rows": len(test),
                "importance_scoring": "average_precision",
                "importance": fold_importances,
            }
        )

    if not fold_results:
        raise SystemExit("No spatial holdout fold contained both classes for permutation importance.")

    aggregate = {
        feature: _summary(values)
        for feature, values in by_feature.items()
        if values
    }
    ranking = sorted(
        (
            {"feature": feature, **stats}
            for feature, stats in aggregate.items()
        ),
        key=lambda row: row["mean"],
        reverse=True,
    )

    report = {
        "schema_version": "mykoknoks-spatial-feature-importance-v1",
        "species": args.species,
        "model_key": args.model,
        "created_at": datetime.now(UTC).isoformat(),
        "method": "permutation importance on grouped spatial holdout folds",
        "scoring": "average_precision",
        "folds_requested": n_splits,
        "folds_evaluated": len(fold_results),
        "repeats": max(2, args.repeats),
        "feature_contract": V1_HABITAT_FEATURE_COLUMNS,
        "fold_results": fold_results,
        "ranking": ranking,
        "calibrated": False,
        "probability_claim_allowed": False,
        "interpretation_only": True,
        "scientific_guardrail": (
            "Permutation importance describes sensitivity of this fitted candidate under the sampled "
            "background and spatial folds. It is not causal attribution and does not establish "
            "biological absence or calibrated occurrence probability."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"report={args.out.resolve()}")


if __name__ == "__main__":
    main()

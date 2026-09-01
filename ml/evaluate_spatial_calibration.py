"""Evaluate calibration inside leakage-resistant nested spatial cross-validation.

This stage can show whether calibration improves Brier score/log loss internally. It does not
unlock probability language: independent spatial validation remains a separate release gate.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold

from compare_spatial_models import MODEL_FACTORIES, RANDOM_STATE
from features import TARGET_COLUMN, V1_HABITAT_FEATURE_COLUMNS


def _round(value: float | None) -> float | None:
    return None if value is None or not math.isfinite(value) else round(float(value), 6)


def _mean(values: list[float]) -> float:
    return float(statistics.fmean(values))


def _ece(y_true: pd.Series, probabilities, bins: int = 10) -> float:
    rows = pd.DataFrame({"y": y_true.to_numpy(), "p": probabilities})
    rows["bin"] = pd.cut(rows["p"], bins=bins, labels=False, include_lowest=True)
    total = len(rows)
    error = 0.0
    for _, group in rows.groupby("bin", observed=True):
        if group.empty:
            continue
        error += (len(group) / total) * abs(float(group["y"].mean()) - float(group["p"].mean()))
    return error


def _metrics(y_true: pd.Series, probabilities) -> dict[str, float | None]:
    two_classes = y_true.nunique() >= 2
    has_positive = int(y_true.sum()) > 0
    return {
        "roc_auc": _round(float(roc_auc_score(y_true, probabilities))) if two_classes else None,
        "pr_auc": _round(float(average_precision_score(y_true, probabilities)))
        if has_positive
        else None,
        "brier_score": _round(float(brier_score_loss(y_true, probabilities))),
        "log_loss": _round(float(log_loss(y_true, probabilities, labels=[0, 1]))),
        "ece_10bin": _round(_ece(y_true, probabilities)),
    }


def _metric_mean(folds: list[dict[str, Any]], arm: str, metric: str) -> float | None:
    values = [fold[arm][metric] for fold in folds if fold[arm][metric] is not None]
    return None if not values else _round(_mean([float(value) for value in values]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--species", required=True)
    parser.add_argument("--model", choices=sorted(MODEL_FACTORIES), default="logistic_regression")
    parser.add_argument("--method", choices=("sigmoid", "isotonic"), default="sigmoid")
    parser.add_argument("--group-column", default="spatial_block")
    parser.add_argument("--outer-folds", type=int, default=5)
    parser.add_argument("--inner-folds", type=int, default=3)
    parser.add_argument("--out", type=Path, default=Path("models/calibration-evaluation.json"))
    args = parser.parse_args()

    required = [*V1_HABITAT_FEATURE_COLUMNS, TARGET_COLUMN, args.group_column]
    frame = pd.read_csv(args.csv).dropna(subset=required).copy()
    if frame.empty or frame[TARGET_COLUMN].nunique() < 2:
        raise SystemExit("Calibration evaluation requires complete presence and background rows.")

    groups = frame[args.group_column].astype(str)
    outer_splits = min(max(2, args.outer_folds), int(groups.nunique()))
    outer = StratifiedGroupKFold(
        n_splits=outer_splits,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    outer_partitions = list(
        outer.split(frame[V1_HABITAT_FEATURE_COLUMNS], frame[TARGET_COLUMN], groups)
    )

    fold_results: list[dict[str, Any]] = []
    factory = MODEL_FACTORIES[args.model]
    for fold_number, (train_idx, test_idx) in enumerate(outer_partitions, start=1):
        train = frame.iloc[train_idx]
        test = frame.iloc[test_idx]
        train_groups = train[args.group_column].astype(str)
        inner_splits = min(max(2, args.inner_folds), int(train_groups.nunique()))
        if inner_splits < 2:
            raise SystemExit("Nested calibration needs at least two spatial groups in each outer train fold.")

        inner = StratifiedGroupKFold(
            n_splits=inner_splits,
            shuffle=True,
            random_state=RANDOM_STATE + fold_number,
        )
        inner_partitions = list(
            inner.split(
                train[V1_HABITAT_FEATURE_COLUMNS],
                train[TARGET_COLUMN],
                train_groups,
            )
        )

        raw_model = factory()
        raw_model.fit(train[V1_HABITAT_FEATURE_COLUMNS], train[TARGET_COLUMN])
        raw_probabilities = raw_model.predict_proba(test[V1_HABITAT_FEATURE_COLUMNS])[:, 1]

        calibrated_model = CalibratedClassifierCV(
            estimator=factory(),
            method=args.method,
            cv=inner_partitions,
        )
        calibrated_model.fit(train[V1_HABITAT_FEATURE_COLUMNS], train[TARGET_COLUMN])
        calibrated_probabilities = calibrated_model.predict_proba(
            test[V1_HABITAT_FEATURE_COLUMNS]
        )[:, 1]

        fold_results.append(
            {
                "fold": fold_number,
                "train_rows": len(train),
                "test_rows": len(test),
                "inner_folds": inner_splits,
                "raw": _metrics(test[TARGET_COLUMN], raw_probabilities),
                "calibrated": _metrics(test[TARGET_COLUMN], calibrated_probabilities),
            }
        )

    summary = {
        arm: {
            metric: _metric_mean(fold_results, arm, metric)
            for metric in ("roc_auc", "pr_auc", "brier_score", "log_loss", "ece_10bin")
        }
        for arm in ("raw", "calibrated")
    }
    raw_brier = summary["raw"]["brier_score"]
    calibrated_brier = summary["calibrated"]["brier_score"]
    raw_loss = summary["raw"]["log_loss"]
    calibrated_loss = summary["calibrated"]["log_loss"]
    internal_gate_passed = bool(
        raw_brier is not None
        and calibrated_brier is not None
        and raw_loss is not None
        and calibrated_loss is not None
        and calibrated_brier <= raw_brier
        and calibrated_loss <= raw_loss
    )

    report = {
        "schema_version": "mykoknoks-calibration-evaluation-v1",
        "species": args.species,
        "model_key": args.model,
        "calibration_method": args.method,
        "created_at": datetime.now(UTC).isoformat(),
        "feature_contract": V1_HABITAT_FEATURE_COLUMNS,
        "target_semantics": "presence versus sampled background, not confirmed biological absence",
        "validation": {
            "method": "nested StratifiedGroupKFold",
            "outer_folds": outer_splits,
            "requested_inner_folds": args.inner_folds,
            "fold_results": fold_results,
        },
        "summary": summary,
        "calibration_gate": {
            "scope": "internal-spatial-cv-only",
            "passed": internal_gate_passed,
            "rule": "calibrated mean Brier <= raw and calibrated mean log loss <= raw",
        },
        "calibrated": False,
        "probability_claim_allowed": False,
        "independent_validation_completed": False,
        "scientific_guardrail": (
            "A passing internal calibration gate is not independent validation. MykoKnoks must not "
            "describe these outputs as calibrated occurrence probabilities until a held-out or "
            "external spatial validation and explicit production calibration gate are completed."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"report={args.out.resolve()}")


if __name__ == "__main__":
    main()

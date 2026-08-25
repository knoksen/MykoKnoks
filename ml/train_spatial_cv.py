"""Train a candidate habitat SDM with grouped spatial cross-validation."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

from features import TARGET_COLUMN, V1_HABITAT_FEATURE_COLUMNS


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _model() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=24,
        l2_regularization=0.8,
        random_state=42,
    )


def _auc(y_true: pd.Series, probabilities) -> float | None:
    if y_true.nunique() < 2:
        return None
    return float(roc_auc_score(y_true, probabilities))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--species", required=True)
    parser.add_argument("--group-column", default="spatial_block")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, default=Path("models/registry"))
    args = parser.parse_args()

    required = [*V1_HABITAT_FEATURE_COLUMNS, TARGET_COLUMN, args.group_column]
    frame = pd.read_csv(args.csv).dropna(subset=required).copy()
    if frame.empty:
        raise SystemExit("No complete rows remain after applying the v1 habitat feature contract.")
    if frame[TARGET_COLUMN].nunique() < 2:
        raise SystemExit("Training requires both presence and explicit background rows.")

    groups = frame[args.group_column].astype(str)
    unique_groups = groups.nunique()
    n_splits = min(max(2, args.folds), unique_groups)
    if n_splits < 2:
        raise SystemExit("Spatial cross-validation requires at least two spatial groups.")

    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=42)
    fold_metrics: list[dict] = []
    for fold, (train_idx, test_idx) in enumerate(
        splitter.split(frame[V1_HABITAT_FEATURE_COLUMNS], frame[TARGET_COLUMN], groups),
        start=1,
    ):
        train = frame.iloc[train_idx]
        test = frame.iloc[test_idx]
        model = _model()
        model.fit(train[V1_HABITAT_FEATURE_COLUMNS], train[TARGET_COLUMN])
        probabilities = model.predict_proba(test[V1_HABITAT_FEATURE_COLUMNS])[:, 1]
        auc = _auc(test[TARGET_COLUMN], probabilities)
        fold_metrics.append(
            {
                "fold": fold,
                "train_rows": len(train),
                "test_rows": len(test),
                "test_groups": int(test[args.group_column].nunique()),
                "roc_auc": None if auc is None else round(auc, 5),
                "average_precision": round(
                    float(average_precision_score(test[TARGET_COLUMN], probabilities)),
                    5,
                ),
                "brier_score": round(
                    float(brier_score_loss(test[TARGET_COLUMN], probabilities)),
                    5,
                ),
            }
        )

    final_model = _model()
    final_model.fit(frame[V1_HABITAT_FEATURE_COLUMNS], frame[TARGET_COLUMN])

    args.out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.species.strip().casefold().replace(" ", "-").replace("/", "-")
    model_id = f"{slug}-spatial-sdm-v1"
    model_path = args.out_dir / f"{model_id}.joblib"
    manifest_path = args.out_dir / f"{model_id}.json"

    joblib.dump(
        {
            "model": final_model,
            "features": V1_HABITAT_FEATURE_COLUMNS,
            "species": args.species,
            "model_id": model_id,
        },
        model_path,
    )

    valid_auc = [item["roc_auc"] for item in fold_metrics if item["roc_auc"] is not None]
    manifest = {
        "id": model_id,
        "name": f"{args.species} spatial habitat SDM candidate",
        "version": "1.0.0",
        "status": "candidate",
        "species": [args.species],
        "model_type": "HistGradientBoostingClassifier",
        "trained": True,
        "calibrated": False,
        "target_semantics": "presence versus operator-supplied background, not confirmed absence",
        "feature_contract": V1_HABITAT_FEATURE_COLUMNS,
        "dataset": {
            "path": str(args.csv),
            "sha256": _sha256(args.csv),
            "rows": len(frame),
            "spatial_groups": int(unique_groups),
            "group_column": args.group_column,
        },
        "cross_validation": {
            "method": "StratifiedGroupKFold",
            "folds": n_splits,
            "fold_metrics": fold_metrics,
            "mean_roc_auc": None
            if not valid_auc
            else round(sum(valid_auc) / len(valid_auc), 5),
            "mean_average_precision": round(
                sum(item["average_precision"] for item in fold_metrics) / len(fold_metrics),
                5,
            ),
            "mean_brier_score": round(
                sum(item["brier_score"] for item in fold_metrics) / len(fold_metrics),
                5,
            ),
        },
        "semantics": (
            "Candidate habitat discrimination model. Background is not biological absence. "
            "Do not call scores calibrated occurrence probabilities until an explicit "
            "calibration stage and independent spatial validation are completed."
        ),
        "created_at": datetime.now(UTC).isoformat(),
        "artifact": str(model_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

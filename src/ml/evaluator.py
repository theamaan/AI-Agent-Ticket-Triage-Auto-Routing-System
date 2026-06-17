"""Evaluation utilities — accuracy, F1, confusion matrix."""
from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline


def evaluate_and_print(
    model: Pipeline,
    X_test: Sequence[str],
    y_test: Sequence[str],
) -> dict:
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print("\n" + "=" * 60)
    print("MODEL EVALUATION REPORT")
    print("=" * 60)
    print(f"  Accuracy  : {acc:.4f} ({acc*100:.1f}%)")
    print(f"  F1 Macro  : {f1_macro:.4f}")
    print(f"  F1 Weighted: {f1_weighted:.4f}")
    print("\nPer-class report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("=" * 60)

    return {
        "accuracy": acc,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
    }


def get_prediction_with_confidence(
    model: Pipeline, text: str
) -> tuple[str, float]:
    """Return (predicted_category, probability) for a single text input."""
    proba = model.predict_proba([text])[0]
    classes = model.classes_
    idx = int(np.argmax(proba))
    return str(classes[idx]), float(proba[idx])

"""
Train TF-IDF + LogisticRegression classifier on sample_tickets.xlsx.
Saves two artefacts:
  src/ml/models/vectorizer.pkl
  src/ml/models/classifier.pkl

Run:  python src/ml/trainer.py
"""
from __future__ import annotations

import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from src.ml.evaluator import evaluate_and_print


TRAINING_DATA_PATH = os.getenv("TRAINING_DATA_PATH", "data/sample_tickets.xlsx")
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "src/ml/models/classifier.pkl")
ML_VECTORIZER_PATH = os.getenv("ML_VECTORIZER_PATH", "src/ml/models/vectorizer.pkl")


def _load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Tickets", engine="openpyxl")
    # Drop rows without category or description
    df = df.dropna(subset=["Description", "Category"])
    df["text"] = df["Summary"].fillna("") + " " + df["Description"].fillna("")
    return df


def train() -> Pipeline:
    print(f"Loading training data from: {TRAINING_DATA_PATH}")
    df = _load_data(TRAINING_DATA_PATH)

    X = df["text"].tolist()
    y = df["Category"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=10_000,
                    sublinear_tf=True,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    C=5.0,
                    solver="lbfgs",
                    multi_class="multinomial",
                    random_state=42,
                ),
            ),
        ]
    )

    print(f"Training on {len(X_train)} samples …")
    pipeline.fit(X_train, y_train)

    # Evaluate
    evaluate_and_print(pipeline, X_test, y_test)

    # Persist artefacts
    model_dir = Path(ML_MODEL_PATH).parent
    model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, ML_MODEL_PATH)
    # Also separately persist vectorizer for inspection
    joblib.dump(pipeline.named_steps["tfidf"], ML_VECTORIZER_PATH)

    print(f"\n✓ Model saved → {ML_MODEL_PATH}")
    print(f"✓ Vectorizer saved → {ML_VECTORIZER_PATH}")
    return pipeline


if __name__ == "__main__":
    train()

"""
services/predictor.py - loads the EXISTING trained model and preprocessing pipeline
(saved in Phase 2) and turns validated inputs into a prediction.

Nothing is retrained here. The saved files are only read.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from models.preprocessing import FEATURE_COLUMNS, ZERO_INVALID_COLUMNS

# Display-only bands for the model score (NOT clinical categories).
LOW_BAND_MAX = 0.33
HIGH_BAND_MIN = 0.66


def risk_band(probability: float) -> str:
    if probability < LOW_BAND_MAX:
        return "Low"
    if probability < HIGH_BAND_MIN:
        return "Moderate"
    return "High"


class Predictor:
    def __init__(self, model_dir: Path, reference_path: Path | None = None):
        model_dir = Path(model_dir)
        files = {
            "model": model_dir / "diabetes_model.pkl",
            "preprocessing": model_dir / "preprocessing_pipeline.pkl",
            "metadata": model_dir / "model_metadata.json",
        }
        for label, path in files.items():
            if not path.exists():
                raise FileNotFoundError(
                    f"Missing {label} file: {path}. Run train_model.py (Phase 2) first "
                    "or set MODEL_DIR in your .env file."
                )

        self.model = joblib.load(files["model"])
        self.preprocessing = joblib.load(files["preprocessing"])
        self.metadata = json.loads(files["metadata"].read_text(encoding="utf-8"))

        if self.metadata.get("feature_order") != FEATURE_COLUMNS:
            raise ValueError("Feature order in model_metadata.json does not match preprocessing.py")

        self.version = self.metadata["model_version"]
        self.threshold = float(self.metadata.get("decision_threshold", 0.5))
        self.reference = self._load_reference(reference_path)

    @staticmethod
    def _load_reference(path) -> dict:
        """Median of each feature in the TRAINING data (zeros treated as missing).

        Used only to draw the comparison chart. Returns {} if the file is missing.
        """
        if not path or not Path(path).exists():
            return {}
        df = pd.read_csv(path)
        df[ZERO_INVALID_COLUMNS] = df[ZERO_INVALID_COLUMNS].replace(0, np.nan)
        return {name: float(df[name].median()) for name in FEATURE_COLUMNS}

    def predict(self, values: dict) -> dict:
        """values: {feature name: number}. Returns class, probability and band."""
        row = np.array([[values[name] for name in FEATURE_COLUMNS]], dtype=float)
        features = self.preprocessing.transform(row)          # same steps as training
        probability = float(self.model.predict_proba(features)[0, 1])
        return {
            "predicted_class": int(probability >= self.threshold),
            "probability": probability,
            "risk_band": risk_band(probability),
            "model_version": self.version,
        }

    def compare(self, values: dict) -> list[dict]:
        """Each input next to the training-data median (for the result chart)."""
        rows = []
        for name in FEATURE_COLUMNS:
            reference = self.reference.get(name)
            value = values[name]
            percent = None
            if reference and value > 0:
                percent = round(value / reference * 100, 1)
            rows.append({"name": name, "value": value, "reference": reference, "percent": percent})
        return rows

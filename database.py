"""
database.py - SQLAlchemy setup and the table that stores prediction history.

Only the 8 health parameters, the model output and a timestamp are stored.
No names, emails or other personal identifiers are collected.
"""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# model feature name -> database column name
COLUMN_MAP = {
    "Pregnancies": "pregnancies",
    "Glucose": "glucose",
    "BloodPressure": "blood_pressure",
    "SkinThickness": "skin_thickness",
    "Insulin": "insulin",
    "BMI": "bmi",
    "DiabetesPedigreeFunction": "diabetes_pedigree",
    "Age": "age",
}


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    pregnancies = db.Column(db.Integer, nullable=False)
    glucose = db.Column(db.Float, nullable=False)
    blood_pressure = db.Column(db.Float, nullable=False)
    skin_thickness = db.Column(db.Float, nullable=False)
    insulin = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    diabetes_pedigree = db.Column(db.Float, nullable=False)
    age = db.Column(db.Integer, nullable=False)

    predicted_class = db.Column(db.Integer, nullable=False)   # 0 or 1
    probability = db.Column(db.Float, nullable=False)         # model score, 0..1
    risk_band = db.Column(db.String(20), nullable=False)      # Low / Moderate / High
    model_version = db.Column(db.String(80), nullable=False)

    @classmethod
    def from_values(cls, values: dict, result: dict) -> "Prediction":
        """Build a row from validated inputs and the predictor's output."""
        columns = {COLUMN_MAP[name]: values[name] for name in COLUMN_MAP}
        return cls(
            **columns,
            predicted_class=result["predicted_class"],
            probability=result["probability"],
            risk_band=result["risk_band"],
            model_version=result["model_version"],
        )

    def inputs(self) -> dict:
        """Return the health parameters keyed by the model's feature names."""
        return {name: getattr(self, column) for name, column in COLUMN_MAP.items()}

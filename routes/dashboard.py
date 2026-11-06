"""routes/dashboard.py - dashboard page and the JSON endpoint feeding its charts.

All numbers come from the predictions actually stored in SQLite (no sample data).
"""
from flask import Blueprint, current_app, jsonify, render_template

from database import Prediction, db

bp = Blueprint("dashboard", __name__)

# (label, lower bound inclusive, upper bound exclusive)
AGE_BINS = [("21-30", 21, 31), ("31-40", 31, 41), ("41-50", 41, 51), ("51-60", 51, 61), ("61+", 61, 200)]
GLUCOSE_BINS = [("<100", 0, 100), ("100-139", 100, 140), ("140-179", 140, 180), ("180+", 180, 1000)]
BMI_BINS = [("<18.5", 0, 18.5), ("18.5-24.9", 18.5, 25), ("25-29.9", 25, 30),
            ("30-34.9", 30, 35), ("35+", 35, 200)]


def _distribution(rows, attribute, bins):
    """Count predictions per bin, split by predicted class."""
    class0, class1 = [0] * len(bins), [0] * len(bins)
    for row in rows:
        value = getattr(row, attribute)
        for index, (_, low, high) in enumerate(bins):
            if low <= value < high:
                (class1 if row.predicted_class == 1 else class0)[index] += 1
                break
    return {"labels": [b[0] for b in bins], "class0": class0, "class1": class1}


def _average(rows, attribute, predicted_class):
    values = [getattr(r, attribute) for r in rows if r.predicted_class == predicted_class]
    return round(sum(values) / len(values), 1) if values else None


@bp.route("/dashboard")
def dashboard():
    total = db.session.scalar(db.select(db.func.count(Prediction.id)))
    return render_template("dashboard.html", total=total,
                           model=current_app.extensions["predictor"].metadata)


@bp.route("/api/dashboard-data")
def dashboard_data():
    rows = db.session.scalars(db.select(Prediction)).all()
    total = len(rows)
    positives = sum(1 for r in rows if r.predicted_class == 1)
    bands = {name: sum(1 for r in rows if r.risk_band == name) for name in ("Low", "Moderate", "High")}
    latest = max((r.created_at for r in rows), default=None)
    return jsonify({
        "total": total,
        "class1": positives,
        "class0": total - positives,
        "average_probability": round(sum(r.probability for r in rows) / total * 100, 1) if total else None,
        "latest": latest.strftime("%d %b %Y, %H:%M") if latest else None,
        "bands": bands,
        "age": _distribution(rows, "age", AGE_BINS),
        "glucose": _distribution(rows, "glucose", GLUCOSE_BINS),
        "bmi": _distribution(rows, "bmi", BMI_BINS),
        "average_glucose": {"class0": _average(rows, "glucose", 0), "class1": _average(rows, "glucose", 1)},
        "average_bmi": {"class0": _average(rows, "bmi", 0), "class1": _average(rows, "bmi", 1)},
    })

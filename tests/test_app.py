"""Tests: model loading, prediction, validation, routes, database, error handling."""
import joblib
import numpy as np
import pytest

from app import create_app
from database import Prediction, db
from models.preprocessing import FEATURE_COLUMNS
from services.validation import validate_form


# ---------- model loading and prediction ----------
def test_model_files_load_and_predict(app):
    predictor = app.extensions["predictor"]
    result = predictor.predict({n: v for n, v in zip(FEATURE_COLUMNS, [2, 120, 70, 20, 80, 28.5, 0.45, 35])})
    assert 0.0 <= result["probability"] <= 1.0
    assert result["predicted_class"] in (0, 1)
    assert result["risk_band"] in ("Low", "Moderate", "High")


def test_prediction_matches_saved_files_directly(app):
    """The app must give exactly what the raw saved pipeline + model give."""
    predictor = app.extensions["predictor"]
    model_dir = app.config["MODEL_DIR"]
    pre = joblib.load(model_dir / "preprocessing_pipeline.pkl")
    model = joblib.load(model_dir / "diabetes_model.pkl")
    values = [6, 148, 72, 35, 0, 33.6, 0.627, 50]
    expected = model.predict_proba(pre.transform(np.array([values], dtype=float)))[0, 1]
    got = predictor.predict(dict(zip(FEATURE_COLUMNS, values)))["probability"]
    assert got == pytest.approx(expected)


def test_missing_model_files_gives_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_app({"TESTING": True, "MODEL_DIR": tmp_path, "SQLALCHEMY_DATABASE_URI": "sqlite://"})


# ---------- validation ----------
def test_validation_accepts_valid_and_zero_unknown(valid_form):
    valid_form.update(Insulin="0", SkinThickness="0")
    values, errors = validate_form(valid_form)
    assert not errors and values["Insulin"] == 0


@pytest.mark.parametrize("field,value", [
    ("Glucose", ""), ("Glucose", "0"), ("Glucose", "abc"), ("Glucose", "nan"), ("Glucose", "inf"),
    ("BMI", "5"), ("Age", "17"), ("Age", "35.5"), ("Pregnancies", "-1"), ("Pregnancies", "99"),
    ("DiabetesPedigreeFunction", "9"),
])
def test_validation_rejects_bad_values(valid_form, field, value):
    valid_form[field] = value
    _, errors = validate_form(valid_form)
    assert field in errors


# ---------- routes ----------
@pytest.mark.parametrize("url", ["/", "/assess", "/dashboard", "/history", "/api/dashboard-data"])
def test_pages_load(client, url):
    assert client.get(url).status_code == 200


def test_home_contains_disclaimer(client):
    assert b"not a medical diagnosis" in client.get("/").data.lower() or b"not</u> a medical" in client.get("/").data


def test_assess_form_has_all_8_fields(client):
    html = client.get("/assess").data.decode()
    for name in FEATURE_COLUMNS:
        assert f'name="{name}"' in html


def test_valid_submission_saves_and_shows_result(client, app, valid_form):
    response = client.post("/assess", data=valid_form)
    assert response.status_code == 302
    page = client.get(response.headers["Location"])
    assert page.status_code == 200 and b"not a medical diagnosis" in page.data.lower()
    with app.app_context():
        row = db.session.scalars(db.select(Prediction)).one()
        assert row.glucose == 120 and row.model_version


def test_invalid_submission_shows_errors_and_saves_nothing(client, app, valid_form):
    valid_form["Glucose"] = "9999"
    response = client.post("/assess", data=valid_form)
    assert response.status_code == 400 and b"Plasma glucose must be between" in response.data
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 0


def test_missing_field_rejected(client, valid_form):
    del valid_form["Age"]
    response = client.post("/assess", data=valid_form)
    assert response.status_code == 400 and b"Age is required" in response.data


def test_history_delete_and_clear(client, app, valid_form):
    for _ in range(2):
        client.post("/assess", data=valid_form)
    assert b"View" in client.get("/history").data
    assert client.post("/history/1/delete").status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 1
    client.post("/history/clear")
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 0


def test_dashboard_api_reflects_real_data(client, valid_form):
    assert client.get("/api/dashboard-data").get_json()["total"] == 0
    client.post("/assess", data=valid_form)
    data = client.get("/api/dashboard-data").get_json()
    assert data["total"] == 1 and data["class0"] + data["class1"] == 1
    assert sum(data["age"]["class0"]) + sum(data["age"]["class1"]) == 1


def test_unknown_pages_return_custom_404(client):
    response = client.get("/nope")
    assert response.status_code == 404 and b"does not exist" in response.data
    assert client.get("/result/9999").status_code == 404


def test_csrf_is_enforced_when_enabled(valid_form):
    app = create_app({"TESTING": True, "CSRF_ENABLED": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    assert app.test_client().post("/assess", data=valid_form).status_code == 400

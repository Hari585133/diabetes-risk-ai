import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from database import db  # noqa: E402

VALID = {"Pregnancies": "2", "Glucose": "120", "BloodPressure": "70", "SkinThickness": "20",
         "Insulin": "80", "BMI": "28.5", "DiabetesPedigreeFunction": "0.45", "Age": "35"}


@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "CSRF_ENABLED": False,
                      "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def valid_form():
    return dict(VALID)

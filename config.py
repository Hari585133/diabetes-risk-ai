"""
config.py - central settings for the Flask app.

Every path can be overridden with an environment variable (or a .env file),
so nothing is hard-coded deep inside the application.
"""
import os
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent          # D:\files

# The saved preprocessing pipeline was pickled with the class path
# 'models.preprocessing.ZeroToNaN'. Putting BASE_DIR on sys.path lets Python
# import that module again when the pipeline is loaded.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")


class Config:
    # Secret key: read from the environment; a random one is generated per start-up
    # if none is set (sessions/CSRF tokens then reset when the server restarts).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # Files created in Phase 1 and Phase 2
    MODEL_DIR = Path(os.environ.get("MODEL_DIR", r"D:\models"))
    REFERENCE_DATA_PATH = Path(
        os.environ.get("REFERENCE_DATA_PATH", r"D:\dataset\processed\train.csv")
    )

    # SQLite database file: D:\files\database\app.db
    DATABASE_DIR = BASE_DIR / "database"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + (DATABASE_DIR / "app.db").as_posix()
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CSRF_ENABLED = True
    HISTORY_PER_PAGE = 15

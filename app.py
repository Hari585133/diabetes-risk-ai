"""
app.py - Flask application factory and entry point.

Run:  python app.py        (then open http://127.0.0.1:5000)
"""
import hmac
import os
import secrets

from flask import Flask, abort, render_template, request, session

from config import Config
from database import db
from routes import dashboard, main, prediction
from services.predictor import Predictor


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    app.config["DATABASE_DIR"].mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    # Load the trained model ONCE at start-up (fails early with a clear message).
    app.extensions["predictor"] = Predictor(
        app.config["MODEL_DIR"], app.config["REFERENCE_DATA_PATH"]
    )

    app.register_blueprint(main.bp)
    app.register_blueprint(prediction.bp)
    app.register_blueprint(dashboard.bp)

    with app.app_context():
        db.create_all()          # creates the table on first run

    _register_csrf(app)
    _register_error_handlers(app)

    @app.context_processor
    def inject_model_info():
        return {"model_version": app.extensions["predictor"].version}

    return app


def _register_csrf(app: Flask) -> None:
    """Minimal CSRF protection: every POST form must carry the session's token."""

    @app.before_request
    def check_csrf():
        if app.config["CSRF_ENABLED"] and request.method == "POST":
            sent = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400, description="Invalid or missing security token. Please reload the page.")

    @app.context_processor
    def inject_csrf():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        return {"csrf_token": session["csrf_token"]}


def _register_error_handlers(app: Flask) -> None:
    messages = {
        400: "The request could not be processed.",
        404: "The page you are looking for does not exist.",
        500: "An unexpected error occurred. Please try again.",
    }

    def handler(error):
        code = getattr(error, "code", 500)
        message = messages.get(code, "Something went wrong.")
        if code == 400 and getattr(error, "description", None):
            message = error.description
        return render_template("error.html", code=code, message=message), code

    for code in messages:
        app.register_error_handler(code, handler)


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000,
                     debug=os.environ.get("FLASK_DEBUG") == "1")

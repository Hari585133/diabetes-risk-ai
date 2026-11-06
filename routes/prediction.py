"""routes/prediction.py - assessment form, result page and prediction history."""
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for)

from database import Prediction, db
from services.validation import FIELD_SPECS, validate_form

bp = Blueprint("prediction", __name__)


def _predictor():
    return current_app.extensions["predictor"]


@bp.route("/assess", methods=["GET", "POST"])
def assess():
    if request.method == "GET":
        return render_template("assess.html", fields=FIELD_SPECS, form={}, errors={})

    values, errors = validate_form(request.form)
    if errors:
        return render_template("assess.html", fields=FIELD_SPECS,
                               form=request.form, errors=errors), 400
    try:
        result = _predictor().predict(values)
        record = Prediction.from_values(values, result)
        db.session.add(record)
        db.session.commit()
    except Exception:                                   # never show raw errors to users
        db.session.rollback()
        current_app.logger.exception("Prediction failed")
        flash("Something went wrong while generating the prediction. Please try again.", "danger")
        return render_template("assess.html", fields=FIELD_SPECS,
                               form=request.form, errors={}), 500

    return redirect(url_for("prediction.result", prediction_id=record.id))


@bp.route("/result/<int:prediction_id>")
def result(prediction_id):
    record = db.get_or_404(Prediction, prediction_id)
    comparison = _predictor().compare(record.inputs())
    specs = {spec["name"]: spec for spec in FIELD_SPECS}
    chart_data = {
        "probability": round(record.probability * 100, 1),
        "predicted_class": record.predicted_class,
        "labels": [specs[row["name"]]["label"] for row in comparison],
        "percent": [row["percent"] for row in comparison],
    }
    return render_template("result.html", record=record, comparison=comparison,
                           specs=specs, chart_data=chart_data)


@bp.route("/history")
def history():
    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(Prediction).order_by(Prediction.created_at.desc(), Prediction.id.desc()),
        page=page, per_page=current_app.config["HISTORY_PER_PAGE"], error_out=False,
    )
    return render_template("history.html", pagination=pagination)


@bp.route("/history/<int:prediction_id>/delete", methods=["POST"])
def delete_one(prediction_id):
    record = db.get_or_404(Prediction, prediction_id)
    db.session.delete(record)
    db.session.commit()
    flash("Prediction record deleted.", "success")
    return redirect(url_for("prediction.history"))


@bp.route("/history/clear", methods=["POST"])
def clear_all():
    db.session.execute(db.delete(Prediction))
    db.session.commit()
    flash("All prediction history has been deleted.", "success")
    return redirect(url_for("prediction.history"))

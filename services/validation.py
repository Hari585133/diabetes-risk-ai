"""
services/validation.py - the single source of truth for the 8 input fields.

The same FIELD_SPECS list is used to (a) draw the HTML form and (b) validate the
data on the server, so the two can never disagree.
Ranges are plausibility limits to catch typing mistakes; they are not medical
reference ranges.
"""
import math

FIELD_SPECS = [
    {"name": "Pregnancies", "label": "Pregnancies", "unit": "times", "kind": "int",
     "min": 0, "max": 20, "step": "1", "example": "2",
     "help": "Number of times pregnant."},
    {"name": "Glucose", "label": "Plasma glucose", "unit": "mg/dL", "kind": "float",
     "min": 40, "max": 300, "step": "any", "example": "120",
     "help": "Plasma glucose concentration (oral glucose tolerance test in the original dataset)."},
    {"name": "BloodPressure", "label": "Diastolic blood pressure", "unit": "mm Hg", "kind": "float",
     "min": 30, "max": 140, "step": "any", "example": "70",
     "help": "Diastolic blood pressure."},
    {"name": "SkinThickness", "label": "Skin-fold thickness", "unit": "mm", "kind": "float",
     "min": 0, "max": 99, "step": "any", "example": "20",
     "help": "Triceps skin-fold thickness. Enter 0 if unknown - it is treated as missing."},
    {"name": "Insulin", "label": "Serum insulin", "unit": "mu U/mL", "kind": "float",
     "min": 0, "max": 900, "step": "any", "example": "80",
     "help": "2-hour serum insulin. Enter 0 if unknown - it is treated as missing."},
    {"name": "BMI", "label": "Body mass index", "unit": "kg/m2", "kind": "float",
     "min": 10, "max": 70, "step": "any", "example": "28.5",
     "help": "Weight in kg divided by height in metres squared."},
    {"name": "DiabetesPedigreeFunction", "label": "Diabetes pedigree function", "unit": "score",
     "kind": "float", "min": 0.05, "max": 2.5, "step": "any", "example": "0.45",
     "help": "A score of diabetes family history from the original dataset."},
    {"name": "Age", "label": "Age", "unit": "years", "kind": "int",
     "min": 21, "max": 90, "step": "1", "example": "35",
     "help": "The training data covers adults aged 21 and over."},
]


def validate_form(form) -> tuple[dict, dict]:
    """Check every field. Returns (clean_values, errors).

    clean_values is only complete when errors is empty.
    """
    values, errors = {}, {}
    for spec in FIELD_SPECS:
        name, label = spec["name"], spec["label"]
        raw = (form.get(name) or "").strip()

        if raw == "":
            errors[name] = f"{label} is required."
            continue
        if len(raw) > 20:
            errors[name] = f"{label} is not a valid number."
            continue
        try:
            number = int(raw) if spec["kind"] == "int" else float(raw)
        except ValueError:
            kind = "whole number" if spec["kind"] == "int" else "number"
            errors[name] = f"{label} must be a {kind}."
            continue
        if not math.isfinite(number):          # rejects 'nan' and 'inf'
            errors[name] = f"{label} must be a valid number."
            continue
        if not spec["min"] <= number <= spec["max"]:
            errors[name] = f"{label} must be between {spec['min']} and {spec['max']} {spec['unit']}."
            continue
        values[name] = number
    return values, errors

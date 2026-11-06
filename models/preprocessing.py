"""
Shared preprocessing code (used in training AND later by the Flask app).

Why a separate file? The saved Joblib pipeline remembers the *location* of the
custom class below. Keeping it in one importable module guarantees the Flask
app can load the pipeline later.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
]
TARGET_COLUMN = "Outcome"

# In these columns a value of 0 is biologically impossible -> it means "missing".
# (Pregnancies = 0 is valid, so it is NOT in this list.)
ZERO_INVALID_COLUMNS = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]


class ZeroToNaN(BaseEstimator, TransformerMixin):
    """Replace impossible zeros with NaN so the imputer can fill them.

    Being a pipeline step means a user's form input gets the exact same
    treatment as the training data.
    """

    def __init__(self, columns=None, feature_names=None):
        self.columns = columns
        self.feature_names = feature_names

    def fit(self, X, y=None):
        return self  # nothing to learn

    def transform(self, X):
        df = pd.DataFrame(X, columns=self.feature_names).astype(float)
        df[self.columns] = df[self.columns].replace(0, np.nan)
        return df.to_numpy()


def build_preprocessing_pipeline(scale: bool = True) -> Pipeline:
    """Zero->NaN, median imputation, optional StandardScaler.

    Fit on TRAINING data only (done in the training scripts) to avoid leakage.
    Use scale=False for tree-based models, which do not need scaling.
    """
    steps = [
        ("zero_to_nan", ZeroToNaN(columns=ZERO_INVALID_COLUMNS, feature_names=FEATURE_COLUMNS)),
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)

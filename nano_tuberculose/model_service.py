"""
Model service: loads the tuberculosis prediction model(s) and provides
a unified prediction interface for the Flask API.
"""

import os

import joblib
import pandas as pd

# TensorFlow / Keras is imported lazily to avoid forcing it when only the
# logistic regression model is needed.
_tf = None


def _get_tf():
    global _tf
    if _tf is None:
        import tensorflow as tf  # noqa: F811

        _tf = tf
    return _tf


# ---------------------------------------------------------------------------
# Paths – these are relative to the project root (where app.py lives)
# ---------------------------------------------------------------------------
_BASE = os.path.dirname(os.path.abspath(__file__))
_LOGISTIC_PKL = os.path.join(_BASE, "baseline_pipeline_neural_v3.pkl")
_NEURAL_KERAS = os.path.join(
    _BASE, "modelo_redeneural_tuberculose_vFinal_treino2.keras"
)

# Fallback: the notebook also saves under these names
_LOGISTIC_PKL_FALLBACKS = [
    os.path.join(_BASE, "modelo_tuberculose_v2.pkl"),
    os.path.join(_BASE, "baseline_pipeline_treino2.pkl"),
]


# ---------------------------------------------------------------------------
# Expected predictor columns (in the order the pipeline expects)
# ---------------------------------------------------------------------------
PREDICTOR_COLUMNS = [
    "idade_anos",
    "CS_SEXO",
    "CS_GESTANT",
    "CS_RACA",
    "CS_ESCOL_N",
    "SG_UF",
    "TRATAMENTO",
    "POP_LIBER",
    "POP_RUA",
    "POP_SAUDE",
    "POP_IMIG",
    "FORMA",
    "AGRAVALCOO",
    "AGRAVDIABE",
    "AGRAVDOENC",
    "AGRAVOUTRA",
    "HIV",
    "SG_UF_2",
    "TRATSUP_AT",
    "TRANSF",
]


# ---------------------------------------------------------------------------
# Lazy-loading singletons
# ---------------------------------------------------------------------------
_logistic_pipeline = None
_neural_model = None
_neural_preprocessor = None


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def _resolve_path(*candidates: str) -> str:
    """Return the first existing path from *candidates*."""
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        f"Nenhum modelo encontrado. Procurado em: {list(candidates)}"
    )


def load_logistic_pipeline():
    """Load the scikit-learn logistic-regression pipeline (with preprocessing)."""
    global _logistic_pipeline
    if _logistic_pipeline is not None:
        return _logistic_pipeline

    path = _resolve_path(_LOGISTIC_PKL, *_LOGISTIC_PKL_FALLBACKS)
    _logistic_pipeline = joblib.load(path)
    return _logistic_pipeline


def load_neural_model():
    """
    Load the Keras neural network *and* the preprocessor extracted from the
    logistic-regression pipeline.

    Returns
    -------
    tuple[keras.Model, sklearn.compose.ColumnTransformer]
    """
    global _neural_model, _neural_preprocessor
    if _neural_model is not None:
        return _neural_model, _neural_preprocessor

    tf = _get_tf()

    # The preprocessor lives inside the logistic pipeline
    pipeline = load_logistic_pipeline()
    _neural_preprocessor = pipeline.named_steps["preprocessor"]

    keras_path = _resolve_path(_NEURAL_KERAS)
    _neural_model = tf.keras.models.load_model(keras_path)
    return _neural_model, _neural_preprocessor


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_predictors(data: dict) -> list[str]:
    """Check that *data* contains all required predictor keys.

    Returns a list of missing keys (empty = valid).
    """
    missing = [col for col in PREDICTOR_COLUMNS if col not in data]
    return missing


def cast_to_str(X):
    """Helper function embedded in the pickled pipeline.

    Must be importable at module level so joblib can find it when
    unpickling the ColumnTransformer.
    """
    return pd.DataFrame(X).astype(str).replace("nan", "ignorado")


# O pipeline da regressão logística foi serializado no notebook, onde
# cast_to_str vivia no módulo __main__. Sob gunicorn (ou qualquer entrypoint
# diferente deste módulo), __main__ não tem a função e o unpickle do joblib
# falha com: "Can't get attribute 'cast_to_str' on <module '__main__'>".
# Registramos a função em __main__ para o pickle conseguir resolvê-la.
import __main__ as _main_module  # noqa: E402

if not hasattr(_main_module, "cast_to_str"):
    _main_module.cast_to_str = cast_to_str


def _build_dataframe(data: dict) -> pd.DataFrame:
    """Convert a JSON-like dict into a DataFrame the pipeline expects."""
    return pd.DataFrame([data])


# ---------------------------------------------------------------------------
# Prediction functions
# ---------------------------------------------------------------------------
def predict_logistic(data: dict) -> dict:
    """
    Predict using the baseline logistic-regression model.

    Parameters
    ----------
    data : dict
        Keys matching PREDICTOR_COLUMNS. Values may be strings or numbers.

    Returns
    -------
    dict
        {
            "probability_abandono": float (0–100),
            "probability_nao_abandono":     float (0–100),
            "prediction":           0 or 1,
            "prediction_label":     "Cura" | "Abandono",
            "model":                "logistic_regression"
        }
    """
    pipeline = load_logistic_pipeline()
    df = _build_dataframe(data)

    proba = pipeline.predict_proba(df)[0]  # [p_class_0, p_class_1]
    pred = int(pipeline.predict(df)[0])

    return {
        "probability_abandono": round(float(proba[1]) * 100, 2),
        "probability_nao_abandono": round(float(proba[0]) * 100, 2),
        "prediction": pred,
        "prediction_label": "Abandono" if pred == 1 else "Cura",
        "model": "logistic_regression",
    }


def predict_neural(data: dict) -> dict:
    """
    Predict using the Keras neural-network model.

    Parameters
    ----------
    data : dict
        Same as `predict_logistic`.

    Returns
    -------
    dict
        {
            "probability_abandono": float (0–100),
            "probability_nao_abandono":     float (0–100),
            "prediction":           0 or 1,
            "prediction_label":     "Cura" | "Abandono",
            "model":                "neural_network"
        }
    """
    model, preprocessor = load_neural_model()
    df = _build_dataframe(data)

    X_transformed = preprocessor.transform(df)
    proba = float(model.predict(X_transformed, verbose=0)[0][0])
    pred = int(proba > 0.5)

    return {
        "probability_abandono": round(proba * 100, 2),
        "probability_nao_abandono": round((1 - proba) * 100, 2),
        "prediction": pred,
        "prediction_label": "Abandono" if pred == 1 else "Cura",
        "model": "neural_network",
    }


def predict_both(data: dict) -> dict:
    """Return predictions from both models."""
    return {
        "logistic_regression": predict_logistic(data),
        "neural_network": predict_neural(data),
    }

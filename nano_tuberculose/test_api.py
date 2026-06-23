#!/usr/bin/env python3
"""
Test script for the Tuberculosis Prediction API.

Usage:
    python test_api.py              # runs all tests against localhost:5001
    python test_api.py --url http://my-server:8080   # custom URL
"""

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Sample payload – exactly the one from the notebook simulation cell
# ---------------------------------------------------------------------------
VALID_PAYLOAD = {
    "idade_anos": 35,
    "CS_SEXO": "M",
    "CS_GESTANT": "6",
    "CS_RACA": "1",
    "CS_ESCOL_N": "3",
    "SG_UF": "35",
    "TRATAMENTO": "1",
    "POP_LIBER": "2",
    "POP_RUA": "2",
    "POP_SAUDE": "2",
    "POP_IMIG": "2",
    "FORMA": "1",
    "AGRAVALCOO": "2",
    "AGRAVDIABE": "2",
    "AGRAVDOENC": "2",
    "AGRAVOUTRA": "2",
    "HIV": "2",
    "SG_UF_2": "35",
    "TRATSUP_AT": "1",
    "TRANSF": "2",
}

# Missing two required fields on purpose
MISSING_FIELDS_PAYLOAD = {
    "idade_anos": 22,
    "CS_SEXO": "F",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def _post(base: str, route: str, payload: dict | None = None) -> tuple[int, dict]:
    """Send a POST request, return (status_code, parsed_json)."""
    url = f"{base.rstrip('/')}{route}"
    data = json.dumps(payload).encode() if payload else None
    req = Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urlopen(req) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            body = json.loads(raw) if raw else {"error": str(e)}
        except json.JSONDecodeError:
            body = {"error": f"HTTP {e.code}: {raw[:200]}"}
        return e.code, body


def _get(base: str, route: str) -> tuple[int, dict]:
    """Send a GET request."""
    url = f"{base.rstrip('/')}{route}"
    try:
        with urlopen(url) as resp:
            return resp.status, json.loads(resp.read().decode())
    except HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            body = json.loads(raw) if raw else {"error": str(e)}
        except json.JSONDecodeError:
            body = {"error": f"HTTP {e.code}: {raw[:200]}"}
        return e.code, body


def _assert(condition: bool, test_name: str, detail: str = "") -> bool:
    if condition:
        print(f"  {GREEN}✓ PASS{RESET}  {test_name}")
        return True
    else:
        print(f"  {RED}✗ FAIL{RESET}  {test_name}")
        if detail:
            print(f"         {detail}")
        return False


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
def test_health(base: str) -> bool:
    print(f"\n{YELLOW}[1/5] GET /health{RESET}")
    code, body = _get(base, "/health")
    ok = _assert(code == 200, "status 200", f"got {code}")
    ok &= _assert(body.get("status") == "ok", "body.status == 'ok'")
    ok &= _assert("models" in body, "'models' key present")
    for model in ("logistic_regression", "neural_network"):
        ok &= _assert(
            model in body["models"], f"'{model}' in models", str(body["models"])
        )
        model_val = body["models"].get(model, "")
        ok &= _assert(
            model_val == "loaded",
            f"{model} is 'loaded'",
            f"actual: {model_val}",
        )
    return ok


def test_predict_logistic(base: str) -> bool:
    print(f"\n{YELLOW}[2/5] POST /predict/logistic{RESET}")
    code, body = _post(base, "/predict/logistic", VALID_PAYLOAD)
    ok = _assert(code == 200, "status 200", f"got {code} — {body}")
    if code != 200:
        print(f"         Response: {json.dumps(body, indent=2)}")
        return ok
    ok &= _assert("probability_abandono" in body, "probability_abandono present")
    ok &= _assert(
        "probability_nao_abandono" in body, "probability_nao_abandono present"
    )
    ok &= _assert("prediction" in body, "prediction present")
    ok &= _assert(body["prediction"] in (0, 1), "prediction is 0 or 1")
    ok &= _assert(body["prediction_label"] in ("Cura", "Abandono"), "label valid")
    ok &= _assert(body["model"] == "logistic_regression", "model correct")
    ok &= _assert("recommendation" in body, "recommendation present")
    total = body["probability_abandono"] + body["probability_nao_abandono"]
    ok &= _assert(abs(total - 100) < 0.1, "probs sum to ~100", f"sum={total}")
    print(
        f"         Probs: abandono={body['probability_abandono']}%  cura={body['probability_nao_abandono']}%"
    )
    print(
        f"         Label: {body['prediction_label']}  |  rec: {body['recommendation']}"
    )
    return ok


def test_predict_neural(base: str) -> bool:
    print(f"\n{YELLOW}[3/5] POST /predict/neural{RESET}")
    code, body = _post(base, "/predict/neural", VALID_PAYLOAD)
    ok = _assert(code == 200, "status 200", f"got {code} — {body}")
    if code != 200:
        print(f"         Response: {json.dumps(body, indent=2)}")
        return ok
    ok &= _assert("probability_abandono" in body, "probability_abandono present")
    ok &= _assert(body["model"] == "neural_network", "model correct")
    ok &= _assert("recommendation" in body, "recommendation present")
    total = body["probability_abandono"] + body["probability_nao_abandono"]
    ok &= _assert(abs(total - 100) < 0.1, "probs sum to ~100", f"sum={total}")
    print(
        f"         Probs: abandono={body['probability_abandono']}%  cura={body['probability_nao_abandono']}%"
    )
    print(
        f"         Label: {body['prediction_label']}  |  rec: {body['recommendation']}"
    )
    return ok


def test_predict_both(base: str) -> bool:
    print(f"\n{YELLOW}[4/5] POST /predict (both models){RESET}")
    code, body = _post(base, "/predict", VALID_PAYLOAD)
    ok = _assert(code == 200, "status 200", f"got {code} — {body}")
    if code != 200:
        print(f"         Response: {json.dumps(body, indent=2)}")
        return ok
    ok &= _assert("logistic_regression" in body, "logistic_regression key")
    ok &= _assert("neural_network" in body, "neural_network key")
    for model in ("logistic_regression", "neural_network"):
        pred = body[model]
        ok &= _assert("probability_abandono" in pred, f"{model}: prob_abandono")
        ok &= _assert("recommendation" in pred, f"{model}: recommendation")
    return ok


def test_missing_fields(base: str) -> bool:
    print(f"\n{YELLOW}[5/5] POST /predict with missing fields (expect 400){RESET}")
    code, body = _post(base, "/predict", MISSING_FIELDS_PAYLOAD)
    ok = _assert(code == 400, "status 400", f"got {code}")
    ok &= _assert("error" in body, "error message present")
    ok &= _assert("missing_fields" in body, "missing_fields key")
    ok &= _assert("expected_fields" in body, "expected_fields key")
    print(f"         Missing: {body.get('missing_fields')}")
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Test the Tuberculosis Prediction API")
    parser.add_argument("--url", default="http://localhost:5001", help="API base URL")
    args = parser.parse_args()

    print(f"{YELLOW}Testing against: {args.url}{RESET}")

    try:
        _get(args.url, "/health")
    except URLError:
        print(f"{RED}Cannot reach {args.url} — is the server running?{RESET}")
        sys.exit(1)

    results = [
        test_health(args.url),
        test_predict_logistic(args.url),
        test_predict_neural(args.url),
        test_predict_both(args.url),
        test_missing_fields(args.url),
    ]

    passed = sum(results)
    total = len(results)
    print(f"\n{'─' * 50}")
    if passed == total:
        print(f"{GREEN}All {total} tests passed!{RESET}")
    else:
        print(f"{RED}{passed}/{total} passed — {total - passed} failed{RESET}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

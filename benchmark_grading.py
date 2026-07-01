"""
benchmark_grading.py — turn a model's free-text answer into a score.

Models answer in messy ways ("£1.2 million", "1,200,000", "(5,000)", showing their working).
This parses those into a number and grades against the verified truth, with tolerance.
"""
from __future__ import annotations

import re

_MULT = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6,
         "bn": 1e9, "b": 1e9, "billion": 1e9}


def _to_float(s: str):
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.replace("(", "").replace(")", "").replace("£", "").replace(",", "").replace("+", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_number(text):
    if text is None:
        return None
    t = text.strip().lower().replace(",", "")
    if "=" in t:                    # model showed its working: answer after the last '='
        t = t.rsplit("=", 1)[-1].strip()
    m = re.search(r"(-?\(?£?\d+(?:\.\d+)?\)?)\s*(k|thousand|mn|million|m|bn|billion|b)\b", t)
    if m:
        num = _to_float(m.group(1))
        if num is not None:
            return num * _MULT[m.group(2)]
    m = re.search(r"-?\(?£?\d[\d]*(?:\.\d+)?\)?", t)
    if m:
        return _to_float(m.group(0))
    return None


def grade_numeric(model_text, truth, rel_tol=0.01, abs_tol=1.0) -> bool:
    v = parse_number(model_text)
    if v is None or truth is None:
        return False
    if abs(v - truth) <= abs_tol:
        return True
    return truth != 0 and abs(v - truth) / abs(truth) <= rel_tol


def _norm_name(s):
    s = str(s).lower()
    s = re.sub(r"\b(ltd|limited|plc|llp|llc|uk|the|company|co)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)   # strip spaces/punctuation too (models drop them)


def grade_choice(model_text, truth_label) -> bool:
    if not model_text or not truth_label:
        return False
    t, m = _norm_name(truth_label), _norm_name(model_text)
    if len(t) < 3:
        return t in m
    return t in m or m in t


def grade_boolean(model_text, truth_bool) -> bool:
    if not model_text:
        return False
    t = model_text.strip().lower()
    yes, no = re.search(r"\b(yes|true|correct)\b", t), re.search(r"\b(no|false|incorrect)\b", t)
    said = None
    if yes and (not no or yes.start() < no.start()):
        said = True
    elif no:
        said = False
    return said is not None and said == bool(truth_bool)


_NOT_DISCLOSED = ["not disclosed", "not stated", "not provided", "not available", "not shown",
                  "not reported", "cannot be determined", "cannot determine", "no turnover",
                  "not included", "does not disclose", "is not disclosed", "not present",
                  "not applicable", "n/a", "unable to", "not given", "not in these accounts"]
_ND_STRIPPED = ["notdisclosed", "notstated", "notprovided", "notavailable", "notshown",
                "notreported", "cannotbedetermined", "cannotdetermine", "noturnover",
                "notincluded", "doesnotdisclose", "isnotdisclosed", "notpresent",
                "notapplicable", "notgiven", "nofigure", "notintheseaccounts", "unableto"]


def grade_not_disclosed(model_text) -> bool:
    if not model_text:
        return False
    t = model_text.lower()
    if any(p in t for p in _NOT_DISCLOSED):
        return True
    return any(p in re.sub(r"[^a-z]", "", t) for p in _ND_STRIPPED)


def grade(item, model_text) -> bool:
    at = item.get("answer_type")
    if at == "numeric":
        return grade_numeric(model_text, item["answer"],
                             rel_tol=item.get("rel_tol", 0.01), abs_tol=item.get("abs_tol", 1.0))
    if at == "choice":
        return grade_choice(model_text, item["answer"])
    if at == "boolean":
        return grade_boolean(model_text, item["answer"])
    if at == "not_disclosed":
        return grade_not_disclosed(model_text)
    return False

"""Shared utilities for the literature-kg-construction skill.

Pure standard library (Python >= 3.8). No third-party dependencies.
"""
import hashlib
import json
import re
import unicodedata


def load_json(path):
    # utf-8-sig tolerates a BOM, which some editors/tools prepend
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def dump_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


_WS = re.compile(r"\s+")
# characters ignored when matching a quote against paragraph text
_STRIP = re.compile(r"[\s\-‐‑‒–—―.,;:!?()\[\]{}\u3000'\"“”‘’`´/\\_*~^<>=+]+")


def norm(s):
    """Canonical text form: NFKC, lowercase, collapsed whitespace."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    return _WS.sub(" ", s).strip()


def norm_loose(s):
    """Aggressive form for quote matching: drops whitespace and punctuation.

    Tolerates linearised inline formulae / lost subscripts in extracted text.
    """
    return _STRIP.sub("", norm(s))


def quote_in(quote, text):
    """True if `quote` is a (normalised) substring of `text`."""
    q, t = norm_loose(quote), norm_loose(text)
    return bool(q) and q in t


def stable_id(prefix, *keys):
    """Deterministic short id from normalised keys, stable across runs.

    Adding new papers or re-running does not renumber existing nodes/edges.
    """
    h = hashlib.sha1("||".join(norm(k) for k in keys).encode("utf-8")).hexdigest()
    return "{}_{}".format(prefix, h[:10])


def load_paragraph_index(path):
    """Return (para_map, papers) where para_map keys are (source_id, paragraph_id)."""
    data = load_json(path)
    para_map = {}
    for p in data.get("paragraphs", []):
        para_map[(p["source_id"], p["paragraph_id"])] = p
    return para_map, data.get("papers", [])

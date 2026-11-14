"""Contract I/O: config loaders and candidates.geojson validation (B0).

Owner: Linh (B). The JSON Schema in ``schemas/candidate.schema.json`` is the contract; this
module adds the cross-field rules that JSON Schema cannot express (geometry == lat/lon, X1
evidence cap, lens ids known to ``config/lenses.yaml``).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
SCHEMA_PATH = REPO_ROOT / "schemas" / "candidate.schema.json"

#: Lenses whose evidence is semi-quantitative only (configuration match, not a full sigma).
SEMIQUANT_LENSES = frozenset({"X1"})
#: Statuses allowed on slides (PLAN DF rule).
SLIDE_STATUSES = frozenset({"engine-confirmed", "engine-semiquant"})


class CandidateValidationError(ValueError):
    """Raised when a candidates file breaks the contract. ``errors`` lists every problem found."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"{len(errors)} contract error(s):\n- " + "\n- ".join(errors))


def load_yaml(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=None)
def _load_config(name: str) -> Any:
    return load_yaml(CONFIG_DIR / name)


def load_lenses() -> dict[str, dict]:
    """Return lenses keyed by id (``L1``, ``L2``, ``M1``, ``X1``)."""
    return {lens["id"]: lens for lens in _load_config("lenses.yaml")}


def load_targets() -> dict[str, dict]:
    """Return every planetary target keyed by id, with ``body`` filled in."""
    raw = _load_config("targets.yaml")
    out: dict[str, dict] = {}
    for body, items in raw.items():
        for item in items:
            out[item["id"]] = {**item, "body": body}
    return out


def load_controls() -> list[dict]:
    return list(_load_config("controls.yaml")["controls"])


def min_scale_for(lens: dict, descriptor: str, target_value: float | None = None) -> float:
    """Resolve the physical tolerance of one descriptor (number, ``{rel: x}`` or ``default``)."""
    spec = lens.get("min_scale", {})
    value = spec.get(descriptor, spec.get("default"))
    if value is None:
        raise KeyError(f"lens {lens['id']}: no min_scale for {descriptor}")
    if isinstance(value, dict):
        if target_value is None:
            raise ValueError(f"lens {lens['id']}: {descriptor} min_scale is relative, needs target")
        return float(value["rel"]) * abs(float(target_value))
    return float(value)


@lru_cache(maxsize=1)
def _schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def check_candidates(doc: dict) -> list[str]:
    """Return a list of contract violations for an in-memory FeatureCollection (empty = valid)."""
    validator = jsonschema.Draft202012Validator(_schema())
    errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]
    if errors:
        return errors

    known_lenses = set(load_lenses())
    seen_ids: set[str] = set()
    for i, feat in enumerate(doc["features"]):
        p = feat["properties"]
        where = f"features/{i} ({p['id']})"
        if p["id"] in seen_ids:
            errors.append(f"{where}: duplicate id")
        seen_ids.add(p["id"])
        lon, lat = feat["geometry"]["coordinates"][:2]
        if abs(lon - p["lon"]) > 1e-6 or abs(lat - p["lat"]) > 1e-6:
            errors.append(
                f"{where}: geometry ({lon}, {lat}) != properties lon/lat ({p['lon']}, {p['lat']})"
            )
        if p.get("feature_type") == "site":
            errors += _check_site(p, where)
            continue
        unknown = set(p["lens_scores"]) - known_lenses
        if unknown:
            errors.append(f"{where}: lens ids not in config/lenses.yaml: {sorted(unknown)}")
        if p["evidence_status"] == "engine-confirmed" and set(p["lens_scores"]) <= SEMIQUANT_LENSES:
            errors.append(f"{where}: X1-only candidate is capped at engine-semiquant")
        for lens_id, score in p["lens_scores"].items():
            if score["sigma_capped"] and score["no_analog"] is False and score["sigma"] < 2:
                errors.append(f"{where}: {lens_id} sigma_capped but sigma < 2")
    return errors


#: Attention above this means "well known" (same threshold as discovery.ATTENTION_MAX).
SITE_ATTENTION_MAX = 10


def _check_site(p: dict, where: str) -> list[str]:
    """B17 cross-field rules for a site feature (2c contract, config/sites.yaml)."""
    errors = []
    confirmed = set(p["lenses_engine_confirmed"])
    if confirmed & SEMIQUANT_LENSES:
        errors.append(f"{where}: X1 can never be engine-confirmed at a site "
                      "(use lenses_engine_semiquant)")
    groups = ("lenses_engine_confirmed", "lenses_engine_semiquant", "lenses_hypothesis")
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            both = set(p[groups[a]]) & set(p[groups[b]])
            if both:
                errors.append(f"{where}: lens {sorted(both)} in both {groups[a]} and {groups[b]}")
    if p["n_cells"] != len(p["member_cells"]):
        errors.append(f"{where}: n_cells {p['n_cells']} != {len(p['member_cells'])} member_cells")
    status = p["hidden_status"].lower()
    if status.startswith("yes") or status == "hidden":
        att = p.get("attention_n")
        if att is None or att > SITE_ATTENTION_MAX:
            errors.append(f"{where}: 'hidden' needs a known attention <= {SITE_ATTENTION_MAX}")
        if p.get("n_in_exclusion", 0) > 0:
            errors.append(f"{where}: a site with cells in an exclusion zone is never hidden")
    return errors


def validate_candidates(path: str | Path) -> int:
    """Validate a candidates GeoJSON file against the contract.

    Returns the number of features. Raises :class:`CandidateValidationError` listing all problems.
    """
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    errors = check_candidates(doc)
    if errors:
        raise CandidateValidationError(errors)
    return len(doc["features"])


def write_candidates(doc: dict, path: str | Path) -> int:
    """Validate then write a FeatureCollection (UTF-8, stable key order). Returns feature count."""
    errors = check_candidates(doc)
    if errors:
        raise CandidateValidationError(errors)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return len(doc["features"])

"""Align L1/L2 control rows with the pre-registered contract ``config/controls.yaml`` (B0).

The L1 chip build (A6) ran before controls.yaml was merged and used a provisional list. This
script, run BEFORE any scoring:
  * marks every existing control/decoy row as ``extra`` (descriptive only, not evaluated);
  * for each controls.yaml entry of the lens, re-labels the matching row (same point within
    2 km) as ``control``/``decoy`` with the contract id and expectations, or computes a new chip
    with the shared library if the point was not built yet.
Nothing is tuned: coordinates, expectations and footprints come verbatim from controls.yaml.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.build_L2 import EARTH_OBLIQUITY, add_astro, snow_free_fraction  # noqa: E402
from scripts.gee.chip_dem import get_chip  # noqa: E402
from similitude.descriptors.terrain import terrain_descriptors  # noqa: E402

DERIVED = ROOT / "data" / "derived"
MATCH_KM = 2.0


def _km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = (
        np.sin((p2 - p1) / 2) ** 2
        + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def contract_entries(lens_id: str) -> list[dict]:
    cfg = yaml.safe_load((ROOT / "config" / "controls.yaml").read_text(encoding="utf-8"))
    return [c for c in cfg["controls"] if c.get("lens_id") == lens_id]


def new_row(entry: dict, lens_id: str, template: pd.Series) -> dict:
    chip, meta = get_chip(entry["lat"], entry["lon"], chip_m=10_000, res_m=30.0)
    desc = terrain_descriptors(chip, 30.0, 30.0, radius_m=6_371_000, footprint_m=4000)
    row = {c: np.nan for c in template.index}
    row.update(desc)
    row.update(
        cell_id="",
        lat=entry["lat"],
        lon=entry["lon"],
        footprint_km=4,
        lens_id=lens_id,
        tier=2,
        L_m=30,
        source=meta["source"],
        in_exclusion_buffer=False,
        qa_flag="ok" if meta["nodata_frac"] < 0.05 else "nodata",
    )
    return row


def reconcile(df: pd.DataFrame, lens_id: str) -> pd.DataFrame:
    df = df.copy()
    for col in ("expected_rgb", "control_id"):
        if col not in df:
            df[col] = ""
    pre = df["sample_role"].isin(["control", "decoy", "positive"])  # idempotent re-runs
    df.loc[pre, "sample_role"] = "extra"
    df.loc[pre, "expected"] = ""
    added = []
    for e in contract_entries(lens_id):
        # controls.yaml roles: positive | decoy  ->  sample_role: control | decoy
        role = "decoy" if e.get("role") == "decoy" else "control"
        cand = df[df["sample_role"] == "extra"]
        dist = _km(cand["lat"].to_numpy(), cand["lon"].to_numpy(), e["lat"], e["lon"])
        if len(cand) and dist.min() <= MATCH_KM:
            idx = cand.index[int(np.argmin(dist))]
        else:
            row = new_row(e, lens_id, df.iloc[0])
            if lens_id == "L2":
                tmp = add_astro(pd.DataFrame([row]), EARTH_OBLIQUITY)
                tmp["cell_id"] = "tmp"
                tmp["snow_free_frac"] = snow_free_fraction(tmp).astype(float)
                row = tmp.iloc[0].to_dict()
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            idx = df.index[-1]
            added.append(e["id"])
        df.loc[
            idx, ["sample_role", "cell_id", "name", "expected", "expected_rgb", "control_id"]
        ] = [
            role,
            f"CTRL_{e['id']}",
            e.get("name", e["id"]),
            e.get("expected", ""),
            e.get("expected_rgb", ""),
            e["id"],
        ]
        df.loc[idx, "source"] = f"{df.loc[idx, 'source']} | controls.yaml"
    print(f"{lens_id}: contract entries {len(contract_entries(lens_id))}, new chips {added}")
    print(
        df[df.sample_role.isin(["control", "decoy", "extra"])][
            ["cell_id", "name", "sample_role", "expected"]
        ].to_string(index=False)
    )
    return df


def main() -> None:
    for lens_id in ("L1", "L2"):
        path = DERIVED / f"earth_{lens_id}.parquet"
        reconcile(pd.read_parquet(path), lens_id).to_parquet(path, index=False)


if __name__ == "__main__":
    main()

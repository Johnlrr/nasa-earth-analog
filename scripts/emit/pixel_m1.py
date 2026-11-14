"""B13 / B14b — M1 per-pixel match (rules pre-registered in lenses.yaml M1.pixel_match, B14a).

Stages (PLAN 2b mandatory order):
  null      the existing B5 null footprints (sample_role == null; NOT re-drawn). Writes the pooled
            null pixel values of every diagnostic parameter (data/raw/m1_pixels/, not committed)
            and their quantiles (data/derived/m1_null_quantiles.json, committed).
  floor     B14b: noise floor = max(q95 of null pixels, 0.01) per diagnostic parameter. Prints the
            YAML block to commit into lenses.yaml BEFORE the control stage.
  controls  M1 controls + decoys (+ Harrat seeds to document the 'empty match'). Requires the
            committed noise floor. Coordinates relocated by A14 are read from
            data/derived/relocated_points.csv when present (both original and relocated reported).
  seeds, rank  candidate footprints (rank = unchanged B5 ASTER-GED mafic set).
Each footprint: one EMIT scene (most valid pixels), every valid 60 m pixel -> shared library
(resample + crism_params_stack) -> per target: pixel matches when EVERY diagnostic parameter
>= frac_of_target * target AND >= noise floor -> 8-connected patches -> matched area.
Output: data/derived/earth_M1_pixels.parquet (one row per cell x target x stage).
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_gee as eg  # noqa: E402

from similitude import io  # noqa: E402
from similitude.descriptors import spectral as sp  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
RAW = io.REPO_ROOT / "data" / "raw" / "m1_pixels"
OUT = DERIVED / "earth_M1_pixels.parquet"
QUANT = DERIVED / "m1_null_quantiles.json"
RELOCATED = DERIVED / "relocated_points.csv"


def rules() -> tuple[dict, dict]:
    lens = io.load_lenses()["M1"]
    return lens, lens["pixel_match"]


def target_values(pm: dict) -> dict[str, dict[str, float]]:
    """Target value of each diagnostic parameter, from the MICA variant declared in B14a."""
    mica = pd.read_parquet(DERIVED / "mica.parquet").set_index(["phase", "variant"])
    out = {}
    for tid, spec in pm["diagnostic"].items():
        tv = spec.get("target_variant", {})
        out[tid] = {p: float(mica.loc[(spec["mica_phase"], tv.get(p, tv.get("default",
                                                                              "numerator"))), p])
                    for p in spec["params"]}
    return out


def diag_params(pm: dict) -> list[str]:
    return sorted({p for spec in pm["diagnostic"].values() for p in spec["params"]})


def pixel_area_km2(lat: float) -> float:
    d = eg.EMIT_DEG * 111.32
    return d * d * float(np.cos(np.radians(lat)))


def process(cell: dict, km: float, ndvi_max: float, pm: dict, tvals: dict, floor: dict | None,
            keep_pixels: bool) -> tuple[list[dict], pd.DataFrame | None]:
    img, meta = eg.best_scene(cell["lat"], cell["lon"], km, ndvi_max)
    base = {"cell_id": cell["cell_id"], "name": cell.get("name", ""), "lat": cell["lat"],
            "lon": cell["lon"], "sample_role": cell["sample_role"], "stage": cell["stage"],
            "scene_id": meta["scene_id"], "date": meta["date"], "coord_note": cell.get("note", "")}
    if img is None or meta["n_valid"] == 0:
        return [{**base, "target_id": t, "n_valid_px": 0, "qa_flag": "no_scene"}
                for t in pm["diagnostic"]], None
    px = eg.footprint_pixels(img, cell["lat"], cell["lon"], km, ndvi_max)
    valid = px["valid"]
    common = sp.resample(eg.wavelengths(), px["refl"][valid])
    params = sp.crism_params_stack(common)
    n_valid = int(valid.sum())
    area = pixel_area_km2(cell["lat"])
    rows = []
    for tid, spec in pm["diagnostic"].items():
        row = {**base, "target_id": tid, "n_valid_px": n_valid,
               "qa_flag": "ok" if n_valid >= io.load_lenses()["M1"]["gates"]["min_valid_pixels"]
               else "low_valid"}
        for p in spec["params"]:
            v = params[p][np.isfinite(params[p])]
            for q in (50, 90, 99):
                row[f"{p}_p{q}"] = float(np.percentile(v, q)) if v.size else np.nan
        if floor is not None:
            ok = np.ones(n_valid, dtype=bool)
            for p in spec["params"]:
                thr = max(pm["frac_of_target"] * tvals[tid][p], floor[p])
                row[f"thr_{p}"] = thr
                ok &= np.nan_to_num(params[p], nan=-np.inf) >= thr
            grid = np.zeros(valid.shape, dtype=bool)
            grid[valid] = ok
            lab, n = ndimage.label(grid, structure=np.ones((3, 3), dtype=int))
            sizes = np.bincount(lab.ravel())[1:] if n else np.array([0])
            frac = float(ok.mean()) if n_valid else 0.0
            row.update(n_matched_px=int(ok.sum()), frac_matched=frac,
                       matched_area_km2=float(ok.sum() * area), n_patches=int(n),
                       largest_patch_km2=float(sizes.max() * area))
            limit = pm["pass_largest_patch_km2"]
            row["passes_patch_rule"] = bool(row["largest_patch_km2"] >= limit)
        rows.append(row)
    dump = None
    if keep_pixels:
        dump = pd.DataFrame({p: params[p].astype(np.float32) for p in diag_params(pm)})
        dump.insert(0, "cell_id", cell["cell_id"])
    return rows, dump


def cells_for(stage: str) -> list[dict]:
    earth = pd.read_parquet(DERIVED / "earth_M1.parquet")
    if stage == "null":
        sel = earth[earth["sample_role"] == "null"]
    elif stage == "controls":
        sel = earth[earth["sample_role"].isin(["control", "decoy"])
                    | earth["cell_id"].isin(["seed_harrat_khaybar", "seed_harrat_rahat"])
                    | earth["cell_id"].str.startswith("seed_semail")]
    elif stage == "seeds":
        sel = earth[(earth["sample_role"] == "seed")
                    & ~earth["cell_id"].isin(["seed_harrat_khaybar", "seed_harrat_rahat"])
                    & ~earth["cell_id"].str.startswith("seed_semail")]
    elif stage == "rank":
        sel = earth[earth["sample_role"] == "rank"]
    else:
        raise ValueError(stage)
    cells = [{"cell_id": r.cell_id, "name": r.name, "lat": r.lat, "lon": r.lon,
              "sample_role": r.sample_role, "stage": stage, "note": "original"}
             for r in sel.itertuples()]
    if stage == "controls" and RELOCATED.exists():
        rel = pd.read_csv(RELOCATED, keep_default_na=False)
        for r in rel.itertuples():
            if f"ctl_{r.point_id}" in set(sel["cell_id"]) or r.point_id in set(sel["cell_id"]):
                cid = r.point_id if r.point_id.startswith("ctl_") else f"ctl_{r.point_id}"
                base = sel[sel["cell_id"] == cid].iloc[0]
                cells.append({"cell_id": f"{cid}__relocated", "name": base["name"],
                              "lat": float(r.lat), "lon": float(r.lon),
                              "sample_role": base["sample_role"], "stage": stage,
                              "note": f"relocated by A14: {getattr(r, 'reason', '')}"})
    return cells


def run(stage: str, workers: int) -> None:
    lens, pm = rules()
    floor = pm.get("noise_floor")
    if stage != "null" and not floor:
        raise SystemExit("noise_floor is not committed in lenses.yaml (run --stage floor, commit "
                         "the value, then rerun) - PLAN B14b ordering")
    tvals = target_values(pm)
    km = float(lens["footprint_km"])
    ndvi_max = float(lens["gates"]["ndvi_max"])
    cells = cells_for(stage)
    print(f"[{stage}] {len(cells)} footprints; targets {tvals}")
    rows, dumps = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(process, c, km, ndvi_max, pm, tvals,
                            None if stage == "null" else floor, stage == "null"): c["cell_id"]
                for c in cells}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                r, dump = fut.result()
            except Exception as exc:  # record and continue
                print(f"  ! {futs[fut]}: {exc}")
                continue
            rows += r
            if dump is not None:
                dumps.append(dump)
            if i % 10 == 0 or i == len(cells):
                print(f"  {i}/{len(cells)}")
    df = pd.DataFrame(rows)
    if OUT.exists():
        old = pd.read_parquet(OUT)
        df = pd.concat([old[old["stage"] != stage], df], ignore_index=True)
    df.to_parquet(OUT, index=False)
    if stage == "null" and dumps:
        RAW.mkdir(parents=True, exist_ok=True)
        pool_df = pd.concat(dumps, ignore_index=True)
        pool_df.to_parquet(RAW / "null_diag_pixels.parquet", index=False)
        q = {p: {f"q{int(k * 100)}": float(np.nanquantile(pool_df[p], k))
                 for k in (0.5, 0.9, 0.95, 0.99)} | {"n_pixels": int(pool_df[p].notna().sum())}
             for p in diag_params(pm)}
        q["n_footprints"] = int(pool_df["cell_id"].nunique())
        QUANT.write_text(json.dumps(q, indent=1), encoding="utf-8")
        print(json.dumps(q, indent=1))
    if stage != "null":
        show = df[df["stage"] == stage]
        cols = ["cell_id", "sample_role", "target_id", "n_valid_px", "n_matched_px",
                "matched_area_km2", "largest_patch_km2", "passes_patch_rule", "coord_note"]
        print(show[[c for c in cols if c in show]].round(3).to_string(index=False))


def floor() -> None:
    _, pm = rules()
    q = json.loads(QUANT.read_text(encoding="utf-8"))
    key = f"q{int(pm['noise_floor_quantile'] * 100)}"
    nf = {p: round(max(q[p][key], pm["noise_floor_min"]), 4) for p in diag_params(pm)}
    print("B14b noise floor (commit into lenses.yaml M1.pixel_match.noise_floor BEFORE controls):")
    print("    noise_floor: {" + ", ".join(f"{k}: {v}" for k, v in nf.items()) + "}")
    print(f"    # from {q['n_footprints']} null footprints, "
          + ", ".join(f"{p} n={q[p]['n_pixels']}" for p in nf))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["null", "floor", "controls", "seeds", "rank"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.stage == "floor":
        floor()
        return
    eg.init()
    run(args.stage, args.workers)


if __name__ == "__main__":
    main()

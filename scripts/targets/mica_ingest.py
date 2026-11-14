"""B2 — ingest CRISM MICA type spectra (Viviano-Beck et al. 2014): M1 targets + Sigma population.

Input : data/raw/mars/mica/crism_typespec_*.{tab,lbl}  (PDS volume MROCR_8001, ~31 spectra)
        Download: https://pds-geosciences.wustl.edu/mro/mro-m-crism-4-typespec-v1/mrocr_8001/data/
Output: data/derived/mica.parquet          one row per (phase, variant) with CRISM params (swir)
        data/derived/mica_spectra.parquet  resampled spectra on COMMON_WL_NM (for SAM / figures)
        data/derived/targets_M1.parquet    contract table: reference rows (one per M1 target)
                                           + population rows (all mineral phases,
                                             is_reference=False)

Variants (PLAN B2): ``numerator`` = "CRISM I/F NUMERATOR CORRECTED" (target pixels, closest in
kind to surface reflectance; default) and ``ratioed`` = "CRISM RATIOED I/F CORRECTED" (numerator /
spectrally bland denominator, isolates the mineral band shape). Same library for both.

Usage: python scripts/targets/mica_ingest.py [--variant numerator|ratioed]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from similitude import io
from similitude.descriptors import spectral as sp

ROOT = io.REPO_ROOT
RAW = ROOT / "data" / "raw" / "mars" / "mica"
DERIVED = ROOT / "data" / "derived"
COLS = ["wl_um", "ratioed_corr", "ratioed", "numerator_corr", "numerator", "denom_corr", "denom"]
VARIANT_COL = {"numerator": "numerator_corr", "ratioed": "ratioed_corr"}
#: Phases that are not minerals relevant to M1 (excluded from the Sigma population).
NON_MINERAL = {"CO2_ICE", "H2O_ICE"}
#: M1 target -> MICA phase (MICA spectra closest to each landing-site mineral class).
TARGET_PHASE = {
    "jezero_margin": "MG_CARBONATE",
    "oxia_planum": "FE_SMECTITE",
    "meridiani": "JAROSITE",
    "nili_fossae_olivine": "FE_OLIVINE",
}
SOURCE = "MRO CRISM MICA type spectra (MROCR_8001, Viviano-Beck et al. 2014)"


def parse_label(path: Path) -> dict:
    text = path.read_text(encoding="latin-1")

    def get(key):
        m = re.search(rf"{key}\s*=\s*\"?([^\"\n<]+)", text)
        return m.group(1).strip() if m else None

    return {
        "phase": get("MRO:TYPESPEC_PHASE"),
        "class_name": get("MRO:TYPESPEC_CLASS_NAME"),
        "mars_lat": float(get("MRO:TYPESPEC_NUM_LAT")),
        "mars_lon": float(get("MRO:TYPESPEC_NUM_LON")),
        "source_product": get("SOURCE_PRODUCT_ID"),
        "reference": get("MRO:TYPESPEC_REF"),
        "lab_analog": get("MRO:TYPESPEC_LAB_ANALOG_ID"),
    }


def read_tab(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLS, skipinitialspace=True)
    df = df.astype(float)
    df = df.mask((df > 10) | (df <= 0))  # PDS missing constants / non-physical
    return df


def ingest(variants=("numerator", "ratioed")) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, spectra = [], []
    for tab in sorted(RAW.glob("crism_typespec_*.tab")):
        meta = parse_label(tab.with_suffix(".lbl"))
        df = read_tab(tab)
        wl_nm = df["wl_um"].to_numpy() * 1000.0
        keep = wl_nm <= sp.GRID_MAX_NM + 5  # cut at 2.49 um, never extrapolate
        for variant in variants:
            refl = df[VARIANT_COL[variant]].to_numpy()
            r = sp.resample(wl_nm[keep], refl[keep])
            params = sp.crism_params(r, subset="swir")
            mica_id = f"mica_{meta['phase'].lower()}"
            rows.append({"mica_id": mica_id, "variant": variant, **meta,
                         "n_valid": int(np.isfinite(r).sum()), **params})
            spectra.append({"mica_id": mica_id, "variant": variant,
                            **{f"r{int(w)}": v for w, v in zip(sp.COMMON_WL_NM, r, strict=True)}})
    return pd.DataFrame(rows), pd.DataFrame(spectra)


def build_targets(mica: pd.DataFrame, variant: str) -> pd.DataFrame:
    lens = io.load_lenses()["M1"]
    targets = io.load_targets()
    m = mica[mica["variant"] == variant].set_index("phase")
    desc = lens["descriptors"]
    out = []
    for tid in lens["targets"]:
        phase = TARGET_PHASE[tid]
        t = targets[tid]
        out.append({"target_id": tid, "body": "mars", "lens_id": "M1",
                    "footprint_id": f"{tid}:{m.loc[phase, 'mica_id']}", "is_reference": True,
                    "lat": t["lat"], "lon": t["lon"], "L_m": np.nan,
                    "source": f"{SOURCE}; phase {phase} ({variant})", "mica_phase": phase,
                    "variant": variant, **{d: m.loc[phase, d] for d in desc}})
    for phase, row in m.iterrows():
        if phase in NON_MINERAL:
            continue
        out.append({"target_id": "mars_mineral_population", "body": "mars", "lens_id": "M1",
                    "footprint_id": row["mica_id"], "is_reference": False,
                    "lat": row["mars_lat"], "lon": row["mars_lon"], "L_m": np.nan,
                    "source": f"{SOURCE}; phase {phase} ({variant})", "mica_phase": phase,
                    "variant": variant, **{d: row[d] for d in desc}})
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="numerator", choices=sorted(VARIANT_COL))
    args = ap.parse_args()
    DERIVED.mkdir(parents=True, exist_ok=True)
    mica, spectra = ingest()
    mica.to_parquet(DERIVED / "mica.parquet", index=False)
    spectra.to_parquet(DERIVED / "mica_spectra.parquet", index=False)
    targets = build_targets(mica, args.variant)
    targets.to_parquet(DERIVED / "targets_M1.parquet", index=False)

    # ---- B2 checks (PLAN): carbonate MIN2295_2480 > 0; olivine OLINDEX highest in group ----
    for variant in ("numerator", "ratioed"):
        v = mica[(mica["variant"] == variant) & ~mica["phase"].isin(NON_MINERAL)]
        v = v.set_index("phase")
        carb = v.loc["MG_CARBONATE", "MIN2295_2480"]
        top_ol = v["OLINDEX"].idxmax()
        print(f"[{variant}] MG_CARBONATE MIN2295_2480 = {carb:.4f} (>0: {carb > 0}); "
              f"OLINDEX max = {top_ol} ({v['OLINDEX'].max():.3f}); "
              f"FE_OLIVINE OLINDEX rank = {int(v['OLINDEX'].rank(ascending=False)['FE_OLIVINE'])}"
              f"/{len(v)}")
    print(f"targets_M1: {int(targets['is_reference'].sum())} reference, "
          f"{int((~targets['is_reference']).sum())} population ({args.variant})")


if __name__ == "__main__":
    main()

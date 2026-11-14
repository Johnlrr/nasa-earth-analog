"""B3 — Spike R2/R3: do CRISM summary parameters computed on EMIT separate real aqueous-mineral
analogs from visual decoys?

G1 criterion for M1 (PLAN B3): Lake Salda and Semail have smaller sigma than Wadi Rum vs the Jezero
target (MICA Mg-carbonate). sigma here is a PROVISIONAL diagonal metric (Bao's fidelity.py / A5 is
not available yet): d = ||(e - t) / max(std_pop, min_scale)||, sigma = chi(1).isf(chi(K).sf(d)).
Population = MICA mineral phases (targets_M1.parquet, is_reference=False).

Output: data/derived/spike_r2.csv, data/derived/spike_r2_spectra.parquet
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_gee as eg  # noqa: E402

from similitude import io  # noqa: E402
from similitude.descriptors import spectral as sp  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"

# (id, name, lat, lon, role) — expectations are in config/controls.yaml (locked before results)
SITES = [
    ("lake_salda", "Lake Salda shoreline (TR)", 37.55, 29.68, "positive"),
    ("semail_a", "Semail ophiolite, Wadi Tayin massif A (OM)", 22.90, 58.50, "seed"),
    ("semail_b", "Semail ophiolite, Wadi Tayin massif B (OM)", 23.05, 58.30, "seed"),
    ("semail_c", "Semail ophiolite, Ibra area (OM)", 22.75, 58.60, "seed"),
    ("wadi_rum", "Wadi Rum sandstone (JO)", 29.58, 35.42, "decoy"),
    ("harrat_khaybar", "Harrat Khaybar basalt (SA)", 25.60, 39.90, "seed"),
    ("matanomadh", "Matanomadh, Kutch (IN)", 23.53, 68.95, "seed"),
]


def provisional_sigma(E: np.ndarray, t: np.ndarray, pop: np.ndarray, min_scale: float):
    scale = np.maximum(np.nanstd(pop, axis=0, ddof=1), min_scale)
    z = (E - t) / scale
    ok = np.isfinite(z)
    d = float(np.sqrt(np.sum(z[ok] ** 2)))
    k = int(ok.sum())
    sigma = float(stats.chi(1).isf(stats.chi(k).sf(d))) if k else np.nan
    return d, sigma, z


def main() -> None:
    eg.init()
    lens = io.load_lenses()["M1"]
    desc = lens["descriptors"]
    tgt = pd.read_parquet(DERIVED / "targets_M1.parquet")
    pop = tgt.loc[~tgt["is_reference"], desc].to_numpy(float)
    refs = tgt[tgt["is_reference"]].set_index("target_id")
    mica_spec = pd.read_parquet(DERIVED / "mica_spectra.parquet")
    mica_spec = mica_spec[mica_spec["variant"] == "numerator"].set_index("mica_id")
    min_scale = float(lens["min_scale"]["default"])

    rows, spectra = [], []
    for sid, name, lat, lon, role in SITES:
        r = eg.footprint_spectrum(lat, lon, km=lens["footprint_km"])
        common = sp.resample(r["wl"], r["refl"])
        params = sp.crism_params(common, subset="swir")
        E = np.array([params[d] for d in desc])
        row = {"site": sid, "name": name, "lat": lat, "lon": lon, "role": role,
               "scene": r["scene_id"], "date": r["date"], "n_valid": r["n_valid"],
               "n_scenes": r["n_scenes"], "seconds": round(r["seconds"], 1)}
        for tid in ("jezero_margin", "nili_fossae_olivine", "oxia_planum", "meridiani"):
            t = refs.loc[tid, desc].to_numpy(float)
            d, s, _ = provisional_sigma(E, t, pop, min_scale)
            row[f"d_{tid}"], row[f"sigma_{tid}"] = round(d, 2), round(s, 2)
            mica_id = refs.loc[tid, "footprint_id"].split(":")[1]
            wl_cols = [f"r{int(w)}" for w in sp.COMMON_WL_NM]
            ref_spec = mica_spec.loc[mica_id, wl_cols].to_numpy(float)
            row[f"sam_{tid}"] = round(sp.sam(common, ref_spec), 3)
        row.update({k: round(v, 4) for k, v in params.items()})
        rows.append(row)
        spectra.append({"site": sid, **{f"r{int(w)}": v for w, v in
                                        zip(sp.COMMON_WL_NM, common, strict=True)}})
        print(f"{sid:15s} n_valid={r['n_valid']:5d} {r['seconds']:.1f}s "
              f"sigma_jezero={row['sigma_jezero_margin']:.2f} sam_jezero={row['sam_jezero_margin']}"
              f" OLINDEX={params['OLINDEX']:.3f} D2300={params['D2300']:.3f} "
              f"MIN2295_2480={params['MIN2295_2480']:.3f}")
    df = pd.DataFrame(rows)
    df.to_csv(DERIVED / "spike_r2.csv", index=False)
    pd.DataFrame(spectra).to_parquet(DERIVED / "spike_r2_spectra.parquet", index=False)

    # rank on raw d (sigma overflows to inf for large d; PLAN: sigma is display-only)
    s = df.set_index("site")["d_jezero_margin"]
    semail_best = s[[i for i in s.index if i.startswith("semail")]].min()
    ok = bool(s["lake_salda"] < s["wadi_rum"] and semail_best < s["wadi_rum"])
    verdict = "PASS" if ok else "FAIL"
    print(f"\nG1/M1 (Salda and Semail d < Wadi Rum vs Jezero): {verdict}  (Salda "
          f"{s['lake_salda']:.2f}, Semail best {semail_best:.2f}, Wadi Rum {s['wadi_rum']:.2f})")


if __name__ == "__main__":
    main()

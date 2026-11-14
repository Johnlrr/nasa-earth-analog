"""B15 — X1 as a 3-condition configuration checklist (G1 review 3.2).

Conditions (thresholds in config/lenses.yaml X1.checklist, set after seeing data, disclosed):
  permafrost      maat_c <= -1
  no_thaw_to_ice  ft_yr <= 20          (exclusion condition)
  dry_overburden  aridity_p_pet <= 0.5
Independent check (registered BEFORE results in controls.yaml): the wet-permafrost decoys
yakutsk_lowland and west_siberia_lowland must fail at least one condition. Axel Heiberg is
reported as is. The DESIGN hypothesis "Pamir-Changtang" is reported as rejected by the data.

Input : data/derived/earth_X1.parquet (B6)   Output: data/derived/x1_checklist.parquet
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from similitude import io
from similitude.descriptors import ice

DERIVED = io.REPO_ROOT / "data" / "derived"
CONDITIONS = ("permafrost", "no_thaw_to_ice", "dry_overburden")


def evaluate(df: pd.DataFrame) -> pd.DataFrame:
    """Add one boolean column per condition, n_met and passes_all (NaN input -> condition False)."""
    out = df.copy()
    if "aridity_p_pet" not in out:
        out["aridity_p_pet"] = [ice.aridity_index(p, e) for p, e in zip(out["p_mm"], out["pet_mm"],
                                                                         strict=True)]
    out["cond_permafrost"] = out["maat_c"].le(-1).fillna(False)
    out["cond_no_thaw_to_ice"] = out["ft_yr"].le(20).fillna(False)
    out["cond_dry_overburden"] = out["aridity_p_pet"].le(0.5).fillna(False)
    conds = out[[f"cond_{c}" for c in CONDITIONS]].astype(bool)
    out["n_met"] = conds.sum(axis=1)
    out["passes_all"] = conds.all(axis=1)
    out["failed"] = [", ".join(c for c in CONDITIONS if not r[f"cond_{c}"]) or "-"
                     for _, r in out.iterrows()]
    if "ice_frac" in out:
        # data-validity filter, same thresholds Bao committed for L1 in A13 (>0.2 exclude,
        # 0.05-0.2 flag): exposed glacier ice has no overburden = wrong configuration.
        out["ice_check"] = np.select(
            [out["ice_frac"].isna(), out["ice_frac"] > 0.2, out["ice_frac"] >= 0.05],
            ["not assessed (outside ESA WorldCover)", "excluded: glacier ice", "flag: some ice"],
            default="ok")
        out["candidate"] = out["passes_all"] & ~out["ice_check"].str.startswith("excluded")
    return out


def ice_fraction(df: pd.DataFrame) -> pd.Series:
    """ESA WorldCover class 70 (snow and ice) fraction in each 10 km footprint (GEE)."""
    import os

    import ee

    ee.Initialize(project=os.environ.get("EE_PROJECT", "nasa-hackthon-kl"))
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map").eq(70).rename("ice")
    vals = {}
    rows = list(df.itertuples())
    for i in range(0, len(rows), 200):
        fc = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([r.lon, r.lat]).buffer(5000).bounds(),
                       {"cell_id": r.cell_id}) for r in rows[i:i + 200]])
        for f in wc.reduceRegions(fc, ee.Reducer.mean(), scale=100).getInfo()["features"]:
            vals[f["properties"]["cell_id"]] = f["properties"].get("mean")
    return df["cell_id"].map(vals).astype(float)


def main() -> None:
    earth = pd.read_parquet(DERIVED / "earth_X1.parquet")
    earth["ice_frac"] = ice_fraction(earth)
    res = evaluate(earth)
    res.to_parquet(DERIVED / "x1_checklist.parquet", index=False)

    cols = ["cell_id", "maat_c", "ft_yr", "aridity_p_pet", "n_met", "failed", "ice_check",
            "qa_flag", "in_exclusion_buffer"]
    named = res[res["sample_role"].isin(["control", "decoy", "seed"])]
    print(named[cols].round(2).to_string(index=False))
    pool = res[res["sample_role"].isin(["rank", "null"])]
    passing = pool[pool["candidate"] & pool["qa_flag"].eq("ok")]
    print(f"\nrank+null cells: {len(pool)}; pass all 3, not glacier, qa ok: {len(passing)}; "
          f"outside exclusion zones: {int((~passing['in_exclusion_buffer'].astype(bool)).sum())}")
    if len(passing):
        print(passing.sort_values("ft_yr")[["cell_id", "lat", "lon", "maat_c", "ft_yr", "ice_check",
                                            "aridity_p_pet", "in_exclusion_buffer"]]
              .round(2).head(15).to_string(index=False))

    dec = res.set_index("cell_id")
    checks = {k: bool(dec.loc[f"ctl_{k}", "n_met"] < 3) for k in
              ("yakutsk_lowland", "west_siberia_lowland")}
    print(f"\nIndependent check - registered decoys fail >= 1 condition: {checks} -> "
          f"{'PASS' if all(checks.values()) else 'FAIL'}")
    pamir = res[res["cell_id"].isin(["seed_east_pamir_murghab", "seed_changtang_north",
                                     "seed_karakul_structure", "seed_qiangtang_east",
                                     "seed_west_kunlun_aksai_chin", "seed_kunlun_pass"])]
    print(f"Pamir-Changtang seeds passing all 3: {int(pamir['passes_all'].sum())}/{len(pamir)} "
          f"(failed: {sorted(set(pamir['failed']))})")
    bv = dec.loc["ctl_beacon_valley"]
    print(f"Beacon Valley (reference): n_met {int(bv['n_met'])}, failed: {bv['failed']}")
    print(f"Axel Heiberg (reported as is): n_met {int(dec.loc['ctl_axel_heiberg_eureka', 'n_met'])}"
          f", failed: {dec.loc['ctl_axel_heiberg_eureka', 'failed']}")


if __name__ == "__main__":
    main()

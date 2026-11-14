"""A15: single source of three-state verdicts -> data/derived/verdicts.parquet.

One row = (lens, target, cell, variable) -> TRANSFERS | NO-ANALOG | UNOBSERVED.
``cell_id == ""`` marks a lens-level row; ``target_id == ""`` applies to every target.
Per-lens rules (PLAN 2b A15, committed before the run):
  L1  cell TRANSFERS slope_roughness when in the A12 robust set (rank/seed cells only);
      cells outside the set get no row; lens-level NO-ANALOG if the set is empty.
  L2  lens-level sun_geometry from fidelity no_analog (value = best sigma);
      cell TRANSFERS shadow_casting when native_rank(d_shadow) >= n_native/2 (rank/seed).
  M1  from earth_M1_pixels + m1_stop_rule.json (B13). Stop rule FAIL -> one lens-level
      NO-ANALOG row per analog target ("method illustration"), no cell TRANSFERS.
      Stop rule PASS -> cell TRANSFERS when largest_patch_km2 >= pass threshold.
      unobserved_targets -> UNOBSERVED. No pixel table -> no M1 rows (never falls back to sigma).
  X1  from x1_checklist (B15): TRANSFERS when all 3 conditions pass and not excluded as
      glacier ice; otherwise NO-ANALOG with the failed conditions. No checklist -> no X1 rows.
  all Transfer Ledger items applying to the lens -> lens-level NO-ANALOG with facility
      (an item may set ``verdict: TRANSFERS`` explicitly, e.g. Mars day length);
      ``unobserved_variables`` in lenses.yaml -> lens-level UNOBSERVED.
A9b (report) and B16 (web) only READ this table.

Usage: .venv/bin/python scripts/build_verdicts.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from similitude import io  # noqa: E402

DERIVED = ROOT / "data" / "derived"
OUT = DERIVED / "verdicts.parquet"
COLUMNS = ["lens_id", "target_id", "cell_id", "test", "variable", "state", "value",
           "reason", "facility"]
STATES = {"TRANSFERS", "NO-ANALOG", "UNOBSERVED"}
CANDIDATE_ROLES = {"rank", "seed"}


def _row(lens: dict, variable: str, state: str, value=np.nan, reason: str = "",
         target_id: str = "", cell_id: str = "", facility: str = "") -> dict:
    return {"lens_id": lens["id"], "target_id": target_id, "cell_id": cell_id,
            "test": lens["name"], "variable": variable, "state": state,
            "value": float(value) if value is not None else np.nan,
            "reason": reason, "facility": facility}


def ledger_rows(lens: dict, items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        if lens["id"] not in (it.get("applies_to") or []):
            continue
        state = str(it.get("verdict", "NO-ANALOG"))
        out.append(_row(lens, str(it["id"]), state, it.get("ratio_target_over_earth"),
                        reason=it.get("consequence", ""),
                        facility=it.get("mitigation", "") if state == "NO-ANALOG" else ""))
    return out


def unobserved_rows(lens: dict) -> list[dict]:
    out = []
    for text in lens.get("unobserved_variables") or []:
        var, _, why = str(text).partition(":")
        out.append(_row(lens, var.strip(), "UNOBSERVED", reason=(why or text).strip()))
    return out


def l1_rows(lens: dict, robust: pd.DataFrame) -> list[dict]:
    out = []
    for tid, sub in robust[robust.sample_role.isin(CANDIDATE_ROLES)].groupby("target_id"):
        member = sub[sub.nms_keep.astype(bool)]
        rule = member.set_rule.iloc[0] if len(member) else "intersection (i)&(ii)&(iii)"
        for r in member.itertuples():
            out.append(_row(
                lens, "slope_roughness", "TRANSFERS", r.score, target_id=tid, cell_id=r.cell_id,
                reason=f"A12 robust set ({rule}); native rank i/ii/iii = "
                       f"{r.nr_i:.0f}/{r.nr_ii:.0f}/{r.nr_iii:.0f} of {r.n_i:.0f}"))
        state = "TRANSFERS" if len(member) else "NO-ANALOG"
        out.append(_row(lens, "slope_roughness", state, len(member), target_id=tid,
                        reason=f"robust set size ({rule}) among {len(sub)} rank/seed cells"))
    return out


def l2_rows(
    lens: dict, fid: pd.DataFrame, earth: pd.DataFrame, targets: pd.DataFrame
) -> list[dict]:
    out = []
    f = fid.merge(earth[["cell_id", "sample_role", "lowsun_frac_daylight"]], on="cell_id")
    ref = targets[targets.is_reference.astype(bool)].set_index("target_id")
    for tid, sub in f.groupby("target_id"):
        best = sub.nsmallest(1, "sigma").iloc[0]
        state = "NO-ANALOG" if bool(best.no_analog) else "TRANSFERS"
        t_low = ref.loc[tid, "lowsun_frac_daylight"] if tid in ref.index else np.nan
        out.append(_row(
            lens, "sun_geometry", state, best.sigma, target_id=tid,
            reason=f"best sigma {best.sigma:.1f} ({best.cell_id}); low-sun fraction of daylight: "
                   f"Earth best {sub.lowsun_frac_daylight.max():.2f} vs target {t_low:.2f}",
            facility="High-latitude summer field site or lighting rig for the solar geometry"))
        cand = sub[sub.sample_role.isin(CANDIDATE_ROLES) & sub.native_rank.notna()]
        ok = cand[cand.native_rank >= cand.n_native / 2]
        for r in ok.itertuples():
            out.append(_row(
                lens, "shadow_casting", "TRANSFERS", r.native_rank, target_id=tid,
                cell_id=r.cell_id,
                reason=f"native rank (d_shadow) {r.native_rank:.0f} of {r.n_native:.0f}; "
                       f"sigma_shadow {r.sigma_shadow:.2f}"))
        out.append(_row(lens, "shadow_casting", "TRANSFERS" if len(ok) else "NO-ANALOG", len(ok),
                        target_id=tid,
                        reason=f"cells with native rank (d_shadow) >= n/2 among {len(cand)}"))
    return out


def m1_rows(lens: dict, stop: dict | None, pixels: pd.DataFrame | None) -> list[dict]:
    out = []
    for tid, why in (lens.get("unobserved_targets") or {}).items():
        out.append(_row(lens, "aqueous_mineral", "UNOBSERVED", target_id=tid, reason=why))
    if stop is None or pixels is None:
        return out  # no pixel table yet: no M1 verdicts at all (never fall back to sigma)
    thr = float(lens["pixel_match"]["pass_largest_patch_km2"])
    passed = stop.get("verdict") == "PASS"
    for tid in lens.get("analog_targets") or []:
        note = (" Low confidence: OLINDEX only, continuum-sensitive."
                if tid == "nili_fossae_olivine" else "")
        if not passed:
            lp = stop.get("largest_patch_km2", {})
            salda = lp.get("ctl_lake_salda__relocated", np.nan)
            out.append(_row(
                lens, "aqueous_mineral", "NO-ANALOG", salda, target_id=tid,
                reason="Pre-registered stop rule FAIL (B13): positive control Lake Salda not "
                       f"reproduced at footprint scale (largest patch {salda:.3f} < {thr} km2). "
                       "Method illustration on 4 sites only; no M1 analog published." + note))
            continue
        sub = pixels[(pixels.target_id == tid) & pixels.sample_role.isin(CANDIDATE_ROLES)
                     & pixels.largest_patch_km2.notna()]
        for r in sub.itertuples():
            ok = r.largest_patch_km2 >= thr
            out.append(_row(
                lens, "aqueous_mineral", "TRANSFERS" if ok else "NO-ANALOG", r.matched_area_km2,
                target_id=tid, cell_id=r.cell_id,
                reason=f"largest patch {r.largest_patch_km2:.2f} km2 (pass >= {thr}); matched "
                       f"area {r.matched_area_km2:.2f} km2." + note))
    return out


def x1_rows(lens: dict, chk: pd.DataFrame | None) -> list[dict]:
    if chk is None:
        return []
    out = []
    tid = lens.get("primary_target", "")
    sub = chk[chk.sample_role.isin(CANDIDATE_ROLES)]  # controls stay in x1_checklist
    for r in sub.itertuples():
        if bool(r.candidate):
            state = "TRANSFERS"
            why = "all 3 conditions met (permafrost, no thaw to ice, dry overburden)"
        elif bool(r.passes_all):
            state, why = "NO-ANALOG", f"3 conditions met but {r.ice_check}"
        else:
            state, why = "NO-ANALOG", f"failed: {r.failed}"
        out.append(_row(lens, "ice_configuration", state, r.n_met, target_id=tid,
                        cell_id=r.cell_id, reason=why + " (thresholds set after seeing data)"))
    n = int(sub.candidate.astype(bool).sum())
    out.append(_row(lens, "ice_configuration", "TRANSFERS" if n else "NO-ANALOG", n,
                    target_id=tid,
                    reason="rank/seed cells meeting all 3 conditions (semi-quantitative)"))
    return out


def check(df: pd.DataFrame) -> None:
    assert list(df.columns) == COLUMNS, df.columns
    assert set(df.state) <= STATES, set(df.state)
    assert not df.duplicated(["lens_id", "target_id", "cell_id", "variable"]).any()


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_parquet(path) if path.exists() else None


def build() -> pd.DataFrame:
    lenses = io.load_lenses()
    ledgers = {b: io.load_yaml(ROOT / "ledger" / f"{b}.yaml")["items"] for b in ("moon", "mars")}
    fid = pd.read_parquet(DERIVED / "fidelity.parquet")
    rows: list[dict] = []
    for lid, lens in lenses.items():
        rows += ledger_rows(lens, ledgers[lens["body"]])
        rows += unobserved_rows(lens)
        if lid == "L1":
            robust = _read(DERIVED / "l1_robust_set.parquet")
            if robust is not None:
                rows += l1_rows(lens, robust)
        elif lid == "L2":
            rows += l2_rows(lens, fid[fid.lens_id == "L2"],
                            pd.read_parquet(DERIVED / "earth_L2.parquet"),
                            pd.read_parquet(DERIVED / "targets_L2.parquet"))
        elif lid == "M1":
            sp = DERIVED / "m1_stop_rule.json"
            stop = json.loads(sp.read_text()) if sp.exists() else None
            rows += m1_rows(lens, stop, _read(DERIVED / "earth_M1_pixels.parquet"))
        elif lid == "X1":
            rows += x1_rows(lens, _read(DERIVED / "x1_checklist.parquet"))
    df = pd.DataFrame(rows, columns=COLUMNS)
    check(df)
    return df


def main() -> None:
    df = build()
    df.to_parquet(OUT, index=False)
    lens_level = df[df.cell_id == ""]
    pd.set_option("display.width", 200)
    print(lens_level[["lens_id", "target_id", "variable", "state", "value"]]
          .round(2).to_string(index=False))
    print("\ncell-level TRANSFERS:")
    print(df[(df.cell_id != "") & (df.state == "TRANSFERS")]
          .groupby(["lens_id", "target_id", "variable"]).size().to_string())
    print(f"\nwrote {OUT.relative_to(ROOT)} ({len(df)} rows)")


if __name__ == "__main__":
    main()

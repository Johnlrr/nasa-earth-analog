"""PLAN item A8: score every lens with the shared fidelity engine and run the validation harness.

Inputs  : data/derived/earth_<lens>.parquet, targets_<lens>.parquet, config/lenses.yaml
Outputs : data/derived/fidelity.parquet          (contract schema; discovery prefers it)
          data/derived/validation_controls.parquet
          data/derived/validation_null.parquet
          data/derived/validation_sensitivity.parquet
          docs/figures/validation_*.png
Run     : .venv/bin/python scripts/run_all.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from similitude import io  # noqa: E402
from similitude.fidelity import score_lens  # noqa: E402
from similitude.validation import (  # noqa: E402
    control_report,
    null_summary,
    sensitivity_drop_one,
)

DERIVED = ROOT / "data" / "derived"
FIG = ROOT / "docs" / "figures"
LENSES = ("L1", "L2", "M1", "X1")
CONTROLS = yaml.safe_load((ROOT / "config" / "controls.yaml").read_text(encoding="utf-8"))[
    "controls"
]


def load(lens_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    earth = pd.read_parquet(DERIVED / f"earth_{lens_id}.parquet")
    targets = pd.read_parquet(DERIVED / f"targets_{lens_id}.parquet")
    if "qa_flag" in earth:
        earth = earth[earth["qa_flag"].astype(str).eq("ok")].reset_index(drop=True)
    for col in ("name", "expected"):
        if col not in earth:
            earth[col] = ""
    earth["name"] = earth["name"].fillna("")
    earth["expected"] = earth["expected"].fillna("")
    # Pre-registered expectations come from the contract (controls.yaml), never from the tables.
    exp = {c["id"]: c.get("expected", "") for c in CONTROLS if c["lens_id"] == lens_id}
    ids = earth["cell_id"].str.replace(r"^(ctl_|CTRL_)", "", regex=True)
    from_yaml = ids.map(exp)
    earth.loc[from_yaml.notna(), "expected"] = from_yaml[from_yaml.notna()]
    return earth, targets


def plot_controls(rep: pd.DataFrame, nulls: pd.DataFrame) -> None:
    for lens_id, sub in rep.groupby("lens_id"):
        fig, ax = plt.subplots(figsize=(7, 0.45 * len(sub) + 1.5))
        labels = [f"{r.name or r.cell_id} → {r.target_id}" for r in sub.itertuples()]
        colors = ["#2a7" if r.sample_role == "control" else "#c44" for r in sub.itertuples()]
        ax.barh(labels, sub["percentile"].fillna(0), color=colors)
        ax.axvline(90, ls="--", c="grey", lw=1)
        ax.set_xlim(0, 100)
        ax.set_xlabel("percentile vs random bare land (100 = closer than every null cell)")
        ax.set_title(f"{lens_id}: pre-registered controls (green) and decoys (red)")
        fig.tight_layout()
        fig.savefig(FIG / f"validation_controls_{lens_id}.png", dpi=130)
        plt.close(fig)


def main() -> None:
    lenses = io.load_lenses()
    fids, reps, nulls, sens = [], [], [], []
    for lens_id in LENSES:
        lens = lenses[lens_id]
        earth, targets = load(lens_id)
        fid = score_lens(earth, targets, lens)
        fids.append(fid)
        reps.append(control_report(fid, earth))
        nulls.append(null_summary(fid, earth))
        primary = lens.get("primary_target") or fid["target_id"].iloc[0]
        if len(lens["descriptors"]) > 2:
            sens.append(sensitivity_drop_one(earth, targets, lens, primary))
        best = fid[fid["target_id"] == primary].nsmallest(1, "d").iloc[0]
        print(
            f"{lens_id}: {len(earth)} earth cells, targets {sorted(fid.target_id.unique())}; "
            f"best vs {primary}: {best.cell_id} sigma={best.sigma:.2f} "
            f"(capped={bool(best.sigma_capped)}) no_analog={bool(best.no_analog)} "
            f"mode={best.metric_mode}"
        )
    fid_all = pd.concat(fids, ignore_index=True)
    rep_all = pd.concat(reps, ignore_index=True)
    null_all = pd.concat(nulls, ignore_index=True)
    sens_all = pd.concat(sens, ignore_index=True) if sens else pd.DataFrame()

    fid_all.to_parquet(DERIVED / "fidelity.parquet", index=False)
    rep_all.to_parquet(DERIVED / "validation_controls.parquet", index=False)
    null_all.to_parquet(DERIVED / "validation_null.parquet", index=False)
    sens_all.to_parquet(DERIVED / "validation_sensitivity.parquet", index=False)
    FIG.mkdir(parents=True, exist_ok=True)
    plot_controls(rep_all, null_all)

    pd.set_option("display.width", 160)
    print("\n=== Pre-registered controls / decoys ===")
    print(rep_all.round(3).to_string(index=False))
    print("\n=== d by sample_role (median) ===")
    print(
        null_all.pivot_table(index=["lens_id", "target_id"], columns="sample_role", values="50%")
        .round(2)
        .to_string()
    )
    if not sens_all.empty:
        print("\n=== Drop-one-descriptor sensitivity (Jaccard of top-10) ===")
        col = sens_all.columns[-1]
        print(sens_all.groupby("lens_id")[col].agg(["min", "median"]).round(2).to_string())


if __name__ == "__main__":
    main()

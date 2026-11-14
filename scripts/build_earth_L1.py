"""
Build earth_L1.parquet from tier2_L1_selection.csv.

For every row in the selection:
  1. get_chip(lat, lon, chip_m=10_000, res_m=30.0)      # from scripts/gee/chip_dem.py
  2. terrain_descriptors(chip, 30.0, 30.0, radius_m=6_371_000, footprint_m=4000)
                                                          # from similitude.descriptors.terrain

Runs with ThreadPoolExecutor(max_workers=8) — network I/O is the bottleneck.
Checkpoint every 50 chips to data/raw/earth/tier2_L1_partial.parquet.

Output columns (per PLAN schema):
  cell_id, lat, lon, footprint_km, lens_id, tier, L_m, source, qa_flag,
  sample_role, in_exclusion_buffer, name, expected
  + all descriptor columns from terrain_descriptors()

qa_flag:
  "ok"       — nodata_frac < 0.05
  "nodata"   — nodata_frac >= 0.05  (row kept, descriptors still computed)
  "error:<>" — chip fetch or descriptor computation failed (row kept, descriptors NaN)
"""

from __future__ import annotations

import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))  # allow "scripts.gee.chip_dem" when run as a script

from scripts.gee.chip_dem import get_chip  # type: ignore[import]  # noqa: E402
from similitude.descriptors.terrain import terrain_descriptors  # type: ignore[import]  # noqa: E402

log = logging.getLogger(__name__)

SELECTION_CSV = ROOT / "data/derived/tier2_L1_selection.csv"
OUTPUT_PARQUET = ROOT / "data/derived/earth_L1.parquet"
PARTIAL_PARQUET = ROOT / "data/raw/earth/tier2_L1_partial.parquet"
FIGURES_DIR = ROOT / "docs/figures"

CHIP_M = 10_000.0
RES_M = 30.0
RADIUS_M = 6_371_000.0
FOOTPRINT_M = 4_000.0

MAX_WORKERS = 8
CHECKPOINT_EVERY = 50


# ---------------------------------------------------------------------------
# Per-row processing
# ---------------------------------------------------------------------------


def _process_row(row: dict) -> dict:
    lat = float(row["lat"])
    lon = float(row["lon"])
    cell_id = str(row["cell_id"])
    try:
        dem, meta = get_chip(lat, lon, chip_m=CHIP_M, res_m=RES_M)
        nodata_frac = float(meta.get("nodata_frac", 1.0))
        qa_flag = "ok" if nodata_frac < 0.05 else "nodata"
        descriptors = terrain_descriptors(
            dem, RES_M, RES_M, radius_m=RADIUS_M, footprint_m=FOOTPRINT_M
        )
    except Exception as exc:
        short = str(exc)[:200].replace("\n", " ")
        qa_flag = f"error:{short}"
        nodata_frac = float("nan")
        descriptors = {}

    out = {
        "cell_id": cell_id,
        "lat": lat,
        "lon": lon,
        "footprint_km": 4,
        "lens_id": "L1",
        "tier": 2,
        "L_m": RES_M,
        "source": str(row.get("source", "tier1_terrain")),
        "qa_flag": qa_flag,
        "sample_role": str(row["sample_role"]),
        "in_exclusion_buffer": bool(row.get("in_exclusion_buffer", False)),
        "name": str(row.get("name", "")),
        "expected": str(row.get("expected", "")),
    }
    out.update(descriptors)
    return out


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------


def _load_partial() -> pd.DataFrame | None:
    if PARTIAL_PARQUET.exists():
        try:
            return pd.read_parquet(PARTIAL_PARQUET)
        except Exception:
            return None
    return None


def _save_partial(rows: list[dict]) -> None:
    PARTIAL_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_parquet(PARTIAL_PARQUET, index=False, compression="zstd")


# ---------------------------------------------------------------------------
# Validation output
# ---------------------------------------------------------------------------


def _report_and_plot(df: pd.DataFrame) -> None:
    print("\n--- Summary by sample_role ---")
    print(df.groupby("sample_role").size().to_string())
    print("\n--- qa_flag distribution ---")
    qa_counts = (
        df["qa_flag"]
        .apply(lambda x: "ok" if x == "ok" else ("nodata" if x == "nodata" else "error"))
        .value_counts()
    )
    print(qa_counts.to_string())
    total = len(df)
    ok_pct = (df["qa_flag"] == "ok").sum() / total * 100 if total > 0 else 0.0
    print(f"\nqa_flag=ok: {ok_pct:.1f}% (PLAN requires >= 90%)")

    print("\n--- Top 5 'rank' cells ---")
    rank_df = (
        df[df["sample_role"] == "rank"].nsmallest(5, "d_coarse")
        if "d_coarse" in df.columns
        else df[df["sample_role"] == "rank"].head(5)
    )
    if "slope_p50" in df.columns:
        display_cols = ["cell_id", "lat", "lon", "slope_p50", "frac_gt8", "hurst"]
        display_cols = [c for c in display_cols if c in rank_df.columns]
        print(rank_df[display_cols].to_string(index=False))

    print("\n--- Control / Decoy cells ---")
    ctrl_df = df[df["sample_role"].isin(["control", "decoy"])]
    if "slope_p50" in ctrl_df.columns:
        display_cols = [
            "cell_id",
            "name",
            "sample_role",
            "expected",
            "slope_p50",
            "frac_gt8",
            "hurst",
        ]
        display_cols = [c for c in display_cols if c in ctrl_df.columns]
        print(ctrl_df[display_cols].to_string(index=False))

    # Histogram of slope_p50
    if "slope_p50" in df.columns:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 4))
        vals = df["slope_p50"].dropna()
        ax.hist(vals, bins=50, color="#4472C4", edgecolor="white", linewidth=0.3)
        ax.set_xlabel("slope_p50 (°)")
        ax.set_ylabel("Count")
        ax.set_title("Earth L1 — slope_p50 distribution (all sample roles)")
        fig.tight_layout()
        out_path = FIGURES_DIR / "earth_L1_slope_hist.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"\nHistogram saved to {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    t0 = time.monotonic()

    selection = pd.read_csv(SELECTION_CSV, keep_default_na=False, na_values=[""])
    rows_to_process = selection.to_dict(orient="records")

    # Resume from partial checkpoint
    partial = _load_partial()
    done_ids: set[str] = set()
    completed_rows: list[dict] = []
    if partial is not None:
        done_ids = set(partial["cell_id"].tolist())
        completed_rows = partial.to_dict(orient="records")
        log.info("Resuming: %d chips already done", len(done_ids))

    pending = [r for r in rows_to_process if str(r["cell_id"]) not in done_ids]
    log.info("Pending chips: %d", len(pending))

    since_checkpoint = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_row, row): row for row in pending}
        for future in as_completed(futures):
            result = future.result()
            completed_rows.append(result)
            since_checkpoint += 1
            status = result["qa_flag"]
            log.info(
                "[%d/%d] %s — %s",
                len(completed_rows),
                len(rows_to_process),
                result["cell_id"],
                status,
            )
            if since_checkpoint >= CHECKPOINT_EVERY:
                _save_partial(completed_rows)
                since_checkpoint = 0

    # Final save
    df = pd.DataFrame(completed_rows)
    df.to_parquet(OUTPUT_PARQUET, index=False, compression="zstd")

    elapsed = time.monotonic() - t0
    _report_and_plot(df)
    print(f"\nTotal rows: {len(df)}")
    print(f"Output: {OUTPUT_PARQUET}")
    print(f"Elapsed: {elapsed:.0f} s")


if __name__ == "__main__":
    main()

"""
Tests for select_tier2.py — offline (no network).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import helpers from select_tier2 directly
from scripts.select_tier2 import (  # noqa: E402
    BAND_EDGES,
    SEEDS,
    _haversine_km,
    _nms_30km,
    _stratified_null,
)
from scripts.select_tier2 import (  # noqa: E402
    main as select_main,
)

# ---------------------------------------------------------------------------
# NMS tests
# ---------------------------------------------------------------------------


class TestNMS:
    def test_nms_keeps_better_cell_between_two_close_cells(self):
        """Two cells 10 km apart → only the one with smaller d_coarse survives."""
        df = pd.DataFrame(
            {
                "cell_id": ["A", "B"],
                "lat": [0.0, 0.09],  # ~10 km apart
                "lon": [0.0, 0.0],
                "d_coarse": [1.0, 5.0],
            }
        )
        result = _nms_30km(df, "d_coarse")
        assert len(result) == 1
        assert result.iloc[0]["cell_id"] == "A"

    def test_nms_keeps_both_far_cells(self):
        """Two cells 50 km apart → both survive."""
        df = pd.DataFrame(
            {
                "cell_id": ["A", "B"],
                "lat": [0.0, 0.45],  # ~50 km apart
                "lon": [0.0, 0.0],
                "d_coarse": [1.0, 2.0],
            }
        )
        result = _nms_30km(df, "d_coarse")
        assert len(result) == 2

    def test_nms_exactly_30km_boundary_keeps_both(self):
        """Cells exactly 30 km apart are NOT suppressed (< 30 required for suppression)."""
        # ~30 km at equator ≈ 0.27°
        df = pd.DataFrame(
            {
                "cell_id": ["A", "B"],
                "lat": [0.0, 0.0],
                "lon": [0.0, 0.27],
                "d_coarse": [1.0, 2.0],
            }
        )
        dist = _haversine_km(0.0, 0.0, 0.0, 0.27)
        # Only suppress if dist < 30, so verify dist >= 30 and both survive
        if dist >= 30.0:
            result = _nms_30km(df, "d_coarse")
            assert len(result) == 2

    def test_nms_three_cells_chain(self):
        """A(d=1) and B(d=3) within 10 km → B suppressed. C is 50 km from A and 50 km
        from B → C survives. A and C remain."""
        df = pd.DataFrame(
            {
                "cell_id": ["A", "B", "C"],
                # A at (0, 0); B at (0.09, 0) ~10 km from A; C at (0, 0.45) ~50 km from A
                "lat": [0.0, 0.09, 0.0],
                "lon": [0.0, 0.0, 0.45],
                "d_coarse": [1.0, 3.0, 2.0],
            }
        )
        # Verify distances
        assert _haversine_km(0.0, 0.0, 0.09, 0.0) < 30.0, "A-B should be < 30 km"
        assert _haversine_km(0.0, 0.0, 0.0, 0.45) >= 30.0, "A-C should be >= 30 km"
        result = _nms_30km(df, "d_coarse")
        ids = set(result["cell_id"].tolist())
        assert "B" not in ids, "B should be suppressed by closer, better A"
        assert "A" in ids
        assert "C" in ids


# ---------------------------------------------------------------------------
# Stratified null tests
# ---------------------------------------------------------------------------


class TestStratifiedNull:
    def _make_tier1(self, n_per_band: int = 100) -> pd.DataFrame:
        """Build a synthetic tier1 with n_per_band cells per latitude band."""
        rows = []
        for i, (lo, hi) in enumerate(zip(BAND_EDGES[:-1], BAND_EDGES[1:], strict=True)):
            lats = np.linspace(lo + 0.5, hi - 0.5, n_per_band)
            for j, lat in enumerate(lats):
                rows.append(
                    {
                        "cell_id": f"C{i}_{j}",
                        "lat": float(lat),
                        "lon": float(j),
                        "in_exclusion_buffer": False,
                        "d_coarse": float(i * n_per_band + j),
                    }
                )
        return pd.DataFrame(rows)

    def test_null_total_is_200(self):
        tier1 = self._make_tier1(100)
        result = _stratified_null(tier1, exclude_ids=set(), n_total=200, seed=20261114)
        assert len(result) == 200, f"Expected 200 null cells, got {len(result)}"

    def test_null_excludes_rank_ids(self):
        tier1 = self._make_tier1(100)
        rank_ids = set(tier1["cell_id"].tolist()[:50])
        result = _stratified_null(tier1, exclude_ids=rank_ids, n_total=200, seed=20261114)
        assert len(result) == 200
        assert len(set(result["cell_id"]) & rank_ids) == 0, "Null sample contains rank IDs"

    def test_null_no_duplicates(self):
        tier1 = self._make_tier1(200)
        result = _stratified_null(tier1, exclude_ids=set(), n_total=200, seed=20261114)
        assert result["cell_id"].nunique() == 200

    def test_null_reproducible(self):
        tier1 = self._make_tier1(100)
        r1 = _stratified_null(tier1, exclude_ids=set(), n_total=200, seed=20261114)
        r2 = _stratified_null(tier1, exclude_ids=set(), n_total=200, seed=20261114)
        assert set(r1["cell_id"]) == set(r2["cell_id"]), "Null sample is not reproducible"

    def test_null_uses_all_bands(self):
        """Every inhabited latitude band should contribute at least 1 cell."""
        tier1 = self._make_tier1(50)
        result = _stratified_null(tier1, exclude_ids=set(), n_total=200, seed=20261114)
        result_lats = result["lat"].to_numpy()
        for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:], strict=True):
            # Only check bands that actually have cells in tier1
            band_pool = tier1[(tier1["lat"] >= lo) & (tier1["lat"] < hi)]
            if len(band_pool) > 0:
                band_null = result[(result_lats >= lo) & (result_lats < hi)]
                assert len(band_null) > 0, f"No null cells in band [{lo}, {hi})"


# ---------------------------------------------------------------------------
# Seeds fixed
# ---------------------------------------------------------------------------


class TestSeedFixed:
    def test_seeds_names_stable(self):
        """SEEDS list must contain the 6 expected site names."""
        expected_names = {
            "Peary_Land",
            "Harrat_Khaybar",
            "Karakul",
            "Tenoumer",
            "Roter_Kamm",
            "Wolfe_Creek",
        }
        actual_names = {s["name"] for s in SEEDS}
        assert actual_names == expected_names


# ---------------------------------------------------------------------------
# Integration test: run main() with real parquet (skips if data missing)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (ROOT / "data/derived/tier1_terrain.parquet").exists()
    or not (ROOT / "data/derived/targets_L1_coarse.parquet").exists(),
    reason="Real data files not present",
)
class TestIntegration:
    def test_select_main_produces_correct_counts(self):
        """Run select_main and verify: 300 rank, 200 null, no overlap."""
        select_main()
        result = pd.read_csv(ROOT / "data/derived/tier2_L1_selection.csv", keep_default_na=False)
        rank_ids = set(result[result["sample_role"] == "rank"]["cell_id"])
        null_ids = set(result[result["sample_role"] == "null"]["cell_id"])
        assert len(rank_ids) <= 300
        assert len(null_ids) == 200, f"Expected 200 null, got {len(null_ids)}"
        assert len(rank_ids & null_ids) == 0, "Rank and null overlap"
        assert result[result["sample_role"] == "seed"]["name"].nunique() == 6

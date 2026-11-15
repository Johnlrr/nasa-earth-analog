import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import artemis3_lens as a3  # noqa: E402


def test_grid_v2_rule_and_nan_filter():
    z = np.add.outer(np.arange(1200.0), np.arange(1200.0)) * 0.05   # 6 km at 5 m, gentle plane
    win = a3.grid(z)
    assert len(win) == 9                      # 4 km windows on a 1 km grid: 3 x 3
    assert all(w.shape == (133, 133) for _, _, w in win)   # 4 km at the 30 m baseline
    z[:600, :600] = np.nan
    assert len(a3.grid(z)) < 9


def test_regions_are_named_pgda_sites_only():
    assert set(a3.REGIONS) | set(a3.NOT_RUN) == {
        "haworth", "malapert_massif", "nobile_rim_1", "nobile_rim_2", "mons_mouton_plateau",
        "mons_mouton", "de_gerlache_rim_2", "peak_near_cabeus_b", "slater_plain"}

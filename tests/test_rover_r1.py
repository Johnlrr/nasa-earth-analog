"""Geometry of the rover test (R1): great-circle distance and deterministic leg cuts."""
import sys

import numpy as np
import pandas as pd

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import rover_r1 as r  # noqa: E402


def test_great_circle_one_degree_of_latitude():
    assert np.isclose(r.gc(77.0, 18.0, 77.0, 19.0), r.R * np.pi / 180, rtol=1e-9)


def test_great_circle_longitude_shrinks_with_cos_latitude():
    d = r.gc(77.0, 18.4, 77.01, 18.4)
    assert np.isclose(d, r.R * np.radians(0.01) * np.cos(np.radians(18.4)), rtol=1e-4)


def test_legs_cut_at_first_vertex_beyond_length():
    step = np.degrees(100.1 / r.R)            # 100.1 m of latitude per vertex
    t = pd.DataFrame({"lon": np.full(35, 77.0), "lat": 18.0 + step * np.arange(35),
                      "sol": np.arange(35)})
    legs = r.legs(t, 1000.0)
    assert legs[0] == (0, 10) and legs[1] == (10, 20) and legs[2] == (20, 30)
    assert len(legs) == 3                    # the final partial leg is dropped

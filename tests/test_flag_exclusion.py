import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "gee"))
from flag_exclusion import flag, load_zones  # noqa: E402


def test_flags_without_dropping_rows():
    df = pd.DataFrame(
        {
            "lat": [65.0, 75.38, -24.5, -70.0, 37.6],
            "lon": [-18.0, -89.68, -69.0, 10.0, 29.7],
        }
    )
    out = flag(df, load_zones())
    assert len(out) == len(df)
    assert out.in_exclusion_buffer.tolist() == [True, False, True, True, True]
    assert out.exclusion_zone.tolist()[:2] == ["Iceland", ""]

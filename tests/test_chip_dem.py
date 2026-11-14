"""
Unit tests for chip_dem.py — no network required.

Network tests are marked @pytest.mark.network and skipped by default.
To run them: pytest -m network
"""

import sys
from pathlib import Path

import pytest

# Allow importing scripts/gee/chip_dem without installing it as a package
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts" / "gee"))

from chip_dem import _intersecting_tiles, _tile_name, _tile_url, _utm_epsg


class TestTileName:
    def test_north_west(self):
        # (75.38, -89.68): floor lat=75, floor lon=-90 → N75_00_W090_00
        assert _tile_name(75, -90) == "N75_00_W090_00"

    def test_south_east(self):
        # (-24.5, 135.2): floor lat=-25, floor lon=135 → S25_00_E135_00
        assert _tile_name(-25, 135) == "S25_00_E135_00"

    def test_equator_prime_meridian(self):
        assert _tile_name(0, 0) == "N00_00_E000_00"

    def test_negative_lat_negative_lon(self):
        assert _tile_name(-1, -1) == "S01_00_W001_00"

    def test_high_lat(self):
        assert _tile_name(89, 179) == "N89_00_E179_00"


class TestTileNameFromCoords:
    """Verify that the correct tile is selected for given lat/lon pairs."""

    @pytest.mark.parametrize(
        "lat,lon,expected_tile_lat,expected_tile_lon,expected_name",
        [
            # Devon Island: lat=75.38, lon=-89.68 → floor(75)=75, floor(-89.68)=-90
            (75.38, -89.68, 75, -90, "N75_00_W090_00"),
            # Central Australia: lat=-24.5, lon=135.2 → floor(-24.5)=-25, floor(135.2)=135
            (-24.5, 135.2, -25, 135, "S25_00_E135_00"),
        ],
    )
    def test_tile_for_point(self, lat, lon, expected_tile_lat, expected_tile_lon, expected_name):
        import math

        tile_lat = math.floor(lat)
        tile_lon = math.floor(lon)
        assert tile_lat == expected_tile_lat
        assert tile_lon == expected_tile_lon
        assert _tile_name(tile_lat, tile_lon) == expected_name


class TestUtmEpsg:
    def test_north_hemisphere(self):
        # lon=-89.68 → zone = int((-89.68+180)/6)%60+1 = int(90.32/6)%60+1 = 15%60+1 = 16
        # North → 32616
        assert _utm_epsg(75.38, -89.68) == 32616

    def test_south_hemisphere(self):
        # lon=135.2 → zone = int((135.2+180)/6)%60+1 = int(315.2/6)%60+1 = 52%60+1 = 53
        # South → 32753
        assert _utm_epsg(-24.5, 135.2) == 32753

    def test_equator_prime_meridian(self):
        # lon=0 → zone = int(180/6)%60+1 = 30%60+1 = 31; North → 32631
        assert _utm_epsg(0.0, 0.0) == 32631

    def test_south_america(self):
        # lon=-69, lat=-33 → zone = int(111/6)%60+1=18+1=19; South → 32719
        assert _utm_epsg(-33.0, -69.0) == 32719

    def test_north_alaska(self):
        # lon=-150 → zone = int(30/6)%60+1=5+1=6; North → 32606
        assert _utm_epsg(65.0, -150.0) == 32606


class TestIntersectingTiles:
    def test_single_tile_small_chip(self):
        # Small chip at centre of a cell should need only one (or few) tiles
        tiles = _intersecting_tiles(10.5, 10.5, chip_m=1000, pad_deg=0.0)
        assert (10, 10) in tiles

    def test_near_tile_boundary(self):
        # Point near a 1° boundary: lon=-89.68 is close to -90, lat=75.38
        tiles = _intersecting_tiles(75.38, -89.68, chip_m=10_000)
        tile_lats = [t[0] for t in tiles]
        tile_lons = [t[1] for t in tiles]
        assert 75 in tile_lats
        assert -90 in tile_lons

    def test_returns_list(self):
        tiles = _intersecting_tiles(0.0, 0.0, chip_m=10_000)
        assert isinstance(tiles, list)
        assert len(tiles) >= 1


class TestTileUrl:
    def test_north_west_url(self):
        url = _tile_url(75, -90)
        assert "N75" in url
        assert "W090" in url
        assert url.startswith("https://copernicus-dem-30m.s3.amazonaws.com/")

    def test_south_east_url(self):
        url = _tile_url(-25, 135)
        assert "S25" in url
        assert "E135" in url


# ---------------------------------------------------------------------------
# Network tests — skipped by default; run with: pytest -m network
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_network_devon_island(tmp_path):
    """Fetch a small chip over Devon Island — requires internet."""
    from chip_dem import get_chip

    dem, meta = get_chip(75.38, -89.68, chip_m=10_000, cache_dir=str(tmp_path))
    assert dem.ndim == 2
    assert dem.shape[0] > 0
    assert meta["nodata_frac"] < 1.0
    assert len(meta["tiles"]) > 0
    print(
        f"Devon Island: shape={dem.shape}, nodata={meta['nodata_frac']:.3f}, tiles={meta['tiles']}"
    )


@pytest.mark.network
def test_network_cache_hit(tmp_path):
    """Second call should use cache and return identical array."""
    from chip_dem import get_chip

    dem1, meta1 = get_chip(75.38, -89.68, chip_m=10_000, cache_dir=str(tmp_path))
    dem2, meta2 = get_chip(75.38, -89.68, chip_m=10_000, cache_dir=str(tmp_path))
    import numpy as np

    assert np.array_equal(dem1, dem2, equal_nan=True)

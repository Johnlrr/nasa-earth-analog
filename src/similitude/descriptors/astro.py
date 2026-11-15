"""
Astronomical descriptors — geometric sun angle statistics.

Same formula applicable to any body by setting obliquity_deg.
Earth: obliquity_deg=23.44 (default).
Moon: obliquity_deg=1.54.
Mars: obliquity_deg=25.19.
"""
import numpy as np


def low_sun_hours(
    lat_deg: float,
    max_elev_deg: float = 7.0,
    obliquity_deg: float = 23.44,
    n_days: int = 365,
    steps_per_day: int = 288,
    n_az_bins: int = 36,
) -> dict[str, float]:
    """Fraction of time and daylight hours with sun at low elevation (0 < e ≤ max_elev_deg).

    Pure geometric model (no refraction, no terrain). Applicable to any body.

    Returns
    -------
    dict with keys:
        lowsun_frac_time : fraction of all time steps with 0 < e ≤ max_elev_deg.
        lowsun_frac_daylight : fraction of daylight steps with 0 < e ≤ max_elev_deg.
            0 if no daylight.
        lowsun_az_coverage : fraction of n_az_bins azimuth bins covered when 0 < e ≤ max_elev_deg.
        lowsun_hours_yr : lowsun_frac_time × 8766. Meaningful only for Earth.
    """
    lat = np.radians(lat_deg)
    max_elev_rad = np.radians(max_elev_deg)

    days = np.arange(n_days)
    # Solar declination (simple sinusoidal model)
    delta_rad = np.radians(obliquity_deg) * np.sin(2 * np.pi * (days + 0.5) / n_days)  # (n_days,)

    # Hour angles: 0 = solar noon, 2π = one full day
    h = np.linspace(0, 2 * np.pi, steps_per_day, endpoint=False)  # (steps_per_day,)

    # Broadcasting: delta (n_days, 1) × h (1, steps_per_day)
    delta_2d = delta_rad[:, np.newaxis]  # (n_days, 1)
    h_2d = h[np.newaxis, :]  # (1, steps_per_day)

    # Solar elevation angle
    e = np.arcsin(
        np.sin(lat) * np.sin(delta_2d) + np.cos(lat) * np.cos(delta_2d) * np.cos(h_2d)
    )  # (n_days, steps_per_day)

    # Flatten
    e_flat = e.ravel()

    is_lowsun = (e_flat > 0) & (e_flat <= max_elev_rad)
    is_daylight = e_flat > 0

    lowsun_frac_time = float(np.mean(is_lowsun))
    n_daylight = int(np.sum(is_daylight))
    if n_daylight > 0:
        lowsun_frac_daylight = float(np.sum(is_lowsun) / n_daylight)
    else:
        lowsun_frac_daylight = 0.0

    # Azimuth for low-sun steps
    # Solar azimuth (from South, clockwise in standard formula; use from North for coverage)
    # az = atan2(-cos(delta)*sin(h), cos(lat)*sin(delta) - sin(lat)*cos(delta)*cos(h))
    delta_flat = np.repeat(delta_rad, steps_per_day)
    h_flat = np.tile(h, n_days)

    az_flat = np.arctan2(
        -np.cos(delta_flat) * np.sin(h_flat),
        np.cos(lat) * np.sin(delta_flat) - np.sin(lat) * np.cos(delta_flat) * np.cos(h_flat),
    )

    # Only low-sun azimuths
    lowsun_az = az_flat[is_lowsun]

    if lowsun_az.size > 0:
        # Bin into n_az_bins from -pi to pi
        az_deg_lowsun = np.degrees(lowsun_az)
        # Normalize to [0, 360)
        az_deg_lowsun = az_deg_lowsun % 360.0
        bin_indices = (az_deg_lowsun / 360.0 * n_az_bins).astype(int) % n_az_bins
        bins_covered = len(np.unique(bin_indices))
        lowsun_az_coverage = float(bins_covered / n_az_bins)
    else:
        lowsun_az_coverage = 0.0

    lowsun_hours_yr = lowsun_frac_time * 8766.0

    return {
        "lowsun_frac_time": lowsun_frac_time,
        "lowsun_frac_daylight": lowsun_frac_daylight,
        "lowsun_az_coverage": lowsun_az_coverage,
        "lowsun_hours_yr": lowsun_hours_yr,
    }


def low_sun_windows(
    lat_deg: float,
    max_elev_deg: float = 7.0,
    obliquity_deg: float = 23.44,
    n_days: int = 365,
    steps_per_day: int = 288,
    n_az_bins: int = 36,
) -> dict:
    """Calendar view of ``low_sun_hours`` (same geometric model, same 7 deg threshold).

    A *window day* is a day with daylight on which every daylight step has the Sun at or below
    ``max_elev_deg``. Day 0 of the model is the March equinox (declination rising through 0).

    Returns
    -------
    dict with keys:
        window_days : number of window days per year.
        window_first_day, window_last_day : model day index of the first / last window day of
            the longest contiguous run (wrapping across the year end), or None.
        window_lowsun_min_per_day : mean minutes of low Sun per window day.
        window_az_coverage : fraction of n_az_bins azimuth bins swept by the Sun on window days.
        lowsun_min_per_day : mean minutes of low Sun per day over the whole year.
    """
    lat = np.radians(lat_deg)
    delta = np.radians(obliquity_deg) * np.sin(2 * np.pi * (np.arange(n_days) + 0.5) / n_days)
    h = np.linspace(0, 2 * np.pi, steps_per_day, endpoint=False)
    d2, h2 = delta[:, None], h[None, :]
    e = np.arcsin(np.sin(lat) * np.sin(d2) + np.cos(lat) * np.cos(d2) * np.cos(h2))
    az = np.degrees(np.arctan2(-np.cos(d2) * np.sin(h2),
                               np.cos(lat) * np.sin(d2) - np.sin(lat) * np.cos(d2) * np.cos(h2)))
    day = e > 0
    low = day & (e <= np.radians(max_elev_deg))
    win = day.any(axis=1) & (low.sum(axis=1) == day.sum(axis=1))
    step_min = 1440.0 / steps_per_day
    out = {
        "window_days": int(win.sum()),
        "window_first_day": None,
        "window_last_day": None,
        "window_lowsun_min_per_day": float(low[win].sum(axis=1).mean() * step_min) if win.any()
        else 0.0,
        "window_az_coverage": 0.0,
        "lowsun_min_per_day": float(low.sum(axis=1).mean() * step_min),
    }
    if win.any():
        bins = ((az[win][low[win]] % 360.0) / 360.0 * n_az_bins).astype(int) % n_az_bins
        out["window_az_coverage"] = float(len(np.unique(bins)) / n_az_bins)
        # longest contiguous run on the circular year
        w2 = np.concatenate([win, win])
        best, start, run_start = 0, None, None
        for i, v in enumerate(w2):
            if v and run_start is None:
                run_start = i
            if (not v or i == len(w2) - 1) and run_start is not None:
                end = i if not v else i + 1
                if end - run_start > best:
                    best, start = min(end - run_start, n_days), run_start
                run_start = None
        out["window_first_day"] = int(start % n_days)
        out["window_last_day"] = int((start + best - 1) % n_days)
    return out

"""
Terrain descriptors — same formula for Earth, Moon, and Mars.

Module convention: footprint 4 km + 3 km buffer each side → 10 km chip,
applied identically for Earth and Moon.
"""
import numpy as np
from scipy import ndimage
from scipy.ndimage import gaussian_filter


def aggregate_to_baseline(dem: np.ndarray, res_m: float, L_m: float) -> np.ndarray:
    """Aggregate DEM to baseline resolution L_m.

    Parameters
    ----------
    dem : 2-D float array, elevation in metres. NaN = nodata.
    res_m : current pixel size in metres.
    L_m : target baseline in metres.

    Returns
    -------
    float64 array at resolution L_m (approximate if f is non-integer).

    Raises
    ------
    ValueError if L_m < res_m * 0.999 (cannot super-resolve).
    """
    dem = np.asarray(dem, dtype=np.float64)
    if L_m < res_m * 0.999:
        raise ValueError(
            f"Cannot super-resolve: L_m={L_m} < res_m={res_m}. "
            "Target baseline must be >= current resolution."
        )
    if L_m <= res_m * 1.001:
        return dem.copy()

    f = L_m / res_m

    if abs(f - round(f)) < 0.05:
        # Integer (or near-integer) block mean
        k = int(round(f))
        rows, cols = dem.shape
        # Trim to multiples of k
        r_trim = (rows // k) * k
        c_trim = (cols // k) * k
        dem_trim = dem[:r_trim, :c_trim]

        out_rows = r_trim // k
        out_cols = c_trim // k
        result = np.empty((out_rows, out_cols), dtype=np.float64)

        for ri in range(out_rows):
            for ci in range(out_cols):
                block = dem_trim[ri * k : (ri + 1) * k, ci * k : (ci + 1) * k]
                valid = block[~np.isnan(block)]
                if valid.size < block.size * 0.5:
                    result[ri, ci] = np.nan
                else:
                    result[ri, ci] = np.mean(valid)

        return result

    else:
        # Non-integer factor: Gaussian anti-alias + zoom
        sigma = f / 2.0
        # Normalized convolution to handle NaN
        nan_mask = np.isnan(dem)
        filled = np.where(nan_mask, 0.0, dem)
        valid_mask = (~nan_mask).astype(np.float64)

        numerator = gaussian_filter(filled, sigma=sigma)
        denominator = gaussian_filter(valid_mask, sigma=sigma)

        smoothed = np.where(denominator >= 0.1, numerator / denominator, np.nan)

        # Replace remaining NaN with 0 for zoom (will be set back to NaN)
        nan_after = np.isnan(smoothed)
        smoothed_filled = np.where(nan_after, 0.0, smoothed)
        valid_after = (~nan_after).astype(np.float64)

        zoomed = ndimage.zoom(smoothed_filled, 1.0 / f, order=1)
        zoomed_valid = ndimage.zoom(valid_after, 1.0 / f, order=1)

        # Where valid fraction < 0.5, set to NaN
        zoomed = np.where(zoomed_valid < 0.5, np.nan, zoomed)

        return zoomed.astype(np.float64)


def slope_stats(dem: np.ndarray, res_m: float) -> dict[str, float]:
    """Slope statistics over valid pixels.

    Returns
    -------
    dict with keys:
        slope_p50, slope_p90 : median / 90th-percentile slope in degrees.
        frac_gt8, frac_gt15, frac_gt20 : fraction of valid pixels with slope > 8°/15°/20°.
    """
    dem = np.asarray(dem, dtype=np.float64)
    # np.gradient returns (dzdy, dzdx) for 2D array (row axis, col axis)
    dzdy, dzdx = np.gradient(dem, res_m)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))

    # Only use pixels where both dem and slope are valid (no NaN)
    valid_mask = ~np.isnan(dem) & ~np.isnan(slope)
    slope_valid = slope[valid_mask]

    if slope_valid.size == 0:
        return {
            "slope_p50": np.nan,
            "slope_p90": np.nan,
            "frac_gt8": np.nan,
            "frac_gt15": np.nan,
            "frac_gt20": np.nan,
        }

    return {
        "slope_p50": float(np.percentile(slope_valid, 50)),
        "slope_p90": float(np.percentile(slope_valid, 90)),
        "frac_gt8": float(np.mean(slope_valid > 8.0)),
        "frac_gt15": float(np.mean(slope_valid > 15.0)),
        "frac_gt20": float(np.mean(slope_valid > 20.0)),
    }


def roughness_spectrum(
    dem: np.ndarray, res_m: float, scales=(1, 2, 4, 8, 16)
) -> dict[str, float]:
    """RMS roughness at multiple spatial scales (Shepard et al. 2001) with Hurst exponent.

    Returns
    -------
    dict with keys rms_s{s} for each s in scales (metres), and 'hurst'.
    hurst is the slope of log(rms) vs log(lag distance in metres), fitted over
    all scales with rms > 0.
    """
    dem = np.asarray(dem, dtype=np.float64)

    # De-trend: subtract best-fit plane
    rows, cols = dem.shape
    rr, cc = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    valid_mask = ~np.isnan(dem)
    if valid_mask.sum() >= 3:
        # Least-squares fit ax + by + c
        A = np.column_stack(
            [rr[valid_mask].ravel(), cc[valid_mask].ravel(), np.ones(valid_mask.sum())]
        )
        b_vec = dem[valid_mask].ravel()
        coeffs, _, _, _ = np.linalg.lstsq(A, b_vec, rcond=None)
        plane = coeffs[0] * rr + coeffs[1] * cc + coeffs[2]
        z = dem - plane
    else:
        z = dem.copy()

    result = {}
    rms_vals = []
    lag_dists = []

    for s in scales:
        delta = int(s)

        # Along x (column) direction: z[i, j+delta] - z[i, j]
        if delta < cols:
            diff_x = z[:, delta:] - z[:, :-delta]
            v_x = np.sqrt(np.nanmean(diff_x**2))
        else:
            v_x = np.nan

        # Along y (row) direction: z[i+delta, j] - z[i, j]
        if delta < rows:
            diff_y = z[delta:, :] - z[:-delta, :]
            v_y = np.sqrt(np.nanmean(diff_y**2))
        else:
            v_y = np.nan

        if np.isnan(v_x) and np.isnan(v_y):
            nu = np.nan
        elif np.isnan(v_x):
            nu = v_y
        elif np.isnan(v_y):
            nu = v_x
        else:
            nu = np.sqrt((v_x**2 + v_y**2) / 2.0)

        result[f"rms_s{s}"] = float(nu) if not np.isnan(nu) else np.nan

        if not np.isnan(nu) and nu > 0:
            rms_vals.append(np.log(nu))
            lag_dists.append(np.log(s * res_m))

    # Hurst exponent: slope of log(rms) vs log(lag)
    if len(rms_vals) >= 2:
        coeffs = np.polyfit(lag_dists, rms_vals, 1)
        result["hurst"] = float(coeffs[0])
    else:
        result["hurst"] = np.nan

    return result


def shadow_fraction(
    dem: np.ndarray,
    res_m: float,
    sun_elev_deg=(2, 5, 7),
    n_az: int = 16,
    max_dist_m: float = 3000.0,
    radius_m: float | None = None,
    exclude_border_m: float | None = None,
) -> dict[str, float]:
    """Shadow fraction for multiple solar elevations, averaged over azimuths.

    Uses ray-marching to compute horizon elevation H(az) for each pixel in the
    inner region (excluding border of width exclude_border_m, default = max_dist_m).
    A pixel is shadowed at elevation e if H(az) > e.

    Parameters
    ----------
    radius_m : planetary radius in metres for terrain curvature correction.
        Earth = 6_371_000, Moon = 1_737_400, Mars = 3_389_500. None = flat.
    exclude_border_m : border width to exclude from statistics (default = max_dist_m).

    Returns
    -------
    dict with keys shadow_e{e} for each e in sun_elev_deg (fraction 0–1).
    """
    dem = np.asarray(dem, dtype=np.float64)
    rows, cols = dem.shape

    if exclude_border_m is None:
        exclude_border_m = max_dist_m

    border_px = int(np.ceil(exclude_border_m / res_m))

    # Inner region
    r0 = border_px
    r1 = rows - border_px
    c0 = border_px
    c1 = cols - border_px

    if r0 >= r1 or c0 >= c1:
        raise ValueError(
            f"Inner region is empty: chip {rows}x{cols} px at {res_m} m is too small "
            f"for exclude_border_m={exclude_border_m}."
        )

    inner_rows = r1 - r0
    inner_cols = c1 - c0

    # Horizon map for inner region: shape (inner_rows, inner_cols)
    # We accumulate max horizon angle over all azimuths and distances
    # For each azimuth, compute horizon for all inner pixels
    sun_elev_rad = [np.radians(e) for e in sun_elev_deg]

    # Accumulate shadow counts per elevation, per azimuth
    # horizon shape: (inner_rows, inner_cols) — reset per azimuth
    shadow_counts = {e: np.zeros((inner_rows, inner_cols), dtype=np.float64) for e in sun_elev_deg}
    valid_inner = ~np.isnan(dem[r0:r1, c0:c1])

    # Distance steps
    d_steps = np.arange(res_m, max_dist_m + res_m, res_m)

    for k in range(n_az):
        az_deg = k * 360.0 / n_az
        az_rad = np.radians(az_deg)
        # az from North clockwise: row offset = cos(az), col offset = sin(az)
        sin_az = np.sin(az_rad)
        cos_az = np.cos(az_rad)

        # Horizon for each inner pixel: (inner_rows, inner_cols)
        horizon = np.full((inner_rows, inner_cols), -np.inf)

        for d in d_steps:
            di = int(round(d * cos_az / res_m))
            dj = int(round(d * sin_az / res_m))

            if di == 0 and dj == 0:
                continue

            # Compute source indices in full DEM for each inner pixel
            # Inner pixel (ir, ic) maps to dem index (r0+ir, c0+ic)
            # Observer at (r0+ir, c0+ic), target at (r0+ir+di, c0+ic+dj)
            # Build shifted array: target[ir, ic] = dem[r0+ir+di, c0+ic+dj]

            # Row range of targets in full DEM
            tgt_r0 = r0 + di
            tgt_r1 = r1 + di
            tgt_c0 = c0 + dj
            tgt_c1 = c1 + dj

            # Clamp to DEM bounds
            if tgt_r0 >= rows or tgt_r1 <= 0 or tgt_c0 >= cols or tgt_c1 <= 0:
                # All targets out of bounds
                continue

            # Valid inner pixel ranges that have in-bounds targets
            # target row for inner pixel ir: r0 + ir + di
            # need 0 <= r0 + ir + di < rows → ir >= -(r0+di), ir < rows-r0-di
            ir0_valid = max(0, -(r0 + di))
            ir1_valid = min(inner_rows, rows - r0 - di)
            # target col for inner pixel ic: c0 + ic + dj
            # need 0 <= c0 + ic + dj < cols → ic >= -(c0+dj), ic < cols-c0-dj
            ic0_valid = max(0, -(c0 + dj))
            ic1_valid = min(inner_cols, cols - c0 - dj)

            if ir0_valid >= ir1_valid or ic0_valid >= ic1_valid:
                continue

            # Extract observer and target elevations
            obs_sub = dem[r0 + ir0_valid : r0 + ir1_valid, c0 + ic0_valid : c0 + ic1_valid]
            tgt_sub = dem[
                r0 + ir0_valid + di : r0 + ir1_valid + di,
                c0 + ic0_valid + dj : c0 + ic1_valid + dj,
            ]

            # Curvature correction
            if radius_m is not None:
                curve = d**2 / (2.0 * radius_m)
            else:
                curve = 0.0

            # Angle map
            angle_map = np.arctan((tgt_sub - curve - obs_sub) / d)
            # Where either is NaN, angle_map is NaN

            # Update horizon for valid pixels in this sub-region
            h_sub = horizon[ir0_valid:ir1_valid, ic0_valid:ic1_valid]
            # nanmax: take max ignoring NaN in angle_map
            angle_valid = np.where(np.isnan(angle_map), -np.inf, angle_map)
            horizon[ir0_valid:ir1_valid, ic0_valid:ic1_valid] = np.maximum(h_sub, angle_valid)

        # Count shadowed pixels per elevation
        for e, e_rad in zip(sun_elev_deg, sun_elev_rad, strict=False):
            shadowed = (horizon > e_rad) & valid_inner
            shadow_counts[e] += shadowed.astype(np.float64)

    # Average over azimuths
    n_valid = valid_inner.sum()
    result = {}
    for e in sun_elev_deg:
        if n_valid > 0:
            frac = float(shadow_counts[e].sum()) / (n_valid * n_az)
        else:
            frac = 0.0
        result[f"shadow_e{e}"] = frac

    return result


def terrain_descriptors(
    dem: np.ndarray,
    res_m: float,
    L_m: float,
    radius_m: float | None = None,
    footprint_m: float | None = None,
) -> dict[str, float]:
    """Compute all terrain descriptors at baseline L_m.

    Parameters
    ----------
    L_m : REQUIRED baseline resolution in metres. No default.
    footprint_m : if given, slope/roughness computed on central square of this size;
        shadow_fraction uses whole chip with exclude_border_m = (chip_size - footprint_m)/2.

    Returns
    -------
    dict merging slope_stats, roughness_spectrum, shadow_fraction, plus 'L_m' and 'footprint_m'.
    """
    dem = np.asarray(dem, dtype=np.float64)

    # Step 1: aggregate
    dem_base = aggregate_to_baseline(dem, res_m, L_m)
    base_res = L_m

    result: dict[str, float] = {}

    if footprint_m is not None:
        n_rows, n_cols = dem_base.shape
        fp_px = int(round(footprint_m / base_res))
        if fp_px > min(n_rows, n_cols):
            raise ValueError(f"footprint_m={footprint_m} larger than chip {n_rows}x{n_cols} px")
        half = fp_px // 2
        cr, cc = n_rows // 2, n_cols // 2
        dem_fp = dem_base[cr - half : cr + half, cc - half : cc + half]

        result.update(slope_stats(dem_fp, base_res))
        result.update(roughness_spectrum(dem_fp, base_res))

        # Shadow statistics over the central footprint; the rest of the chip is buffer.
        # Use the smaller chip side so the inner region never exceeds the footprint.
        exclude_border_m = (min(n_rows, n_cols) * base_res - footprint_m) / 2.0
        result.update(
            shadow_fraction(
                dem_base, base_res, radius_m=radius_m, exclude_border_m=exclude_border_m
            )
        )
    else:
        result.update(slope_stats(dem_base, base_res))
        result.update(roughness_spectrum(dem_base, base_res))
        result.update(shadow_fraction(dem_base, base_res, radius_m=radius_m))

    result["L_m"] = float(L_m)
    result["footprint_m"] = float(footprint_m) if footprint_m is not None else None

    return result

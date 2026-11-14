import numpy as np


def make_fbm(n: int, H: float, seed: int = 42) -> np.ndarray:
    """Generate fractional Brownian motion surface via spectral synthesis.

    P(k) ∝ k^(-(2H+2)), size n×n, seed fixed.
    """
    rng = np.random.default_rng(seed)
    # Spectral synthesis
    kx = np.fft.fftfreq(n) * n
    ky = np.fft.fftfreq(n) * n
    KX, KY = np.meshgrid(kx, ky, indexing="ij")
    K = np.sqrt(KX**2 + KY**2)
    K[0, 0] = 1  # avoid division by zero
    # Power spectrum P(k) ∝ k^(-(2H+2))
    power = K ** (-(2 * H + 2))
    power[0, 0] = 0  # zero DC component
    # Random phase
    phase = rng.uniform(0, 2 * np.pi, (n, n))
    # Build complex spectrum with conjugate symmetry for real output
    spectrum = np.sqrt(power) * np.exp(1j * phase)
    # IFFT to get surface
    surface = np.real(np.fft.ifft2(spectrum))
    # Normalize to have zero mean
    surface -= surface.mean()
    return surface

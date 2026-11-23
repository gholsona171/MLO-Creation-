"""Procedural noise for the one texture of our own left on the lot: the lawn's concrete edging (pave.py). Every other ground
texture, and every wear mark on the lot, is Rockstar's own (vanilla_tex.py), laid the way Rockstar lays its car lots (pave.py).
numpy only."""
import numpy as np


def band(n, lo, hi, seed):
    """periodic band-pass noise (feature sizes lo..hi pixels), zero mean, unit std."""
    r = np.random.default_rng(seed); f = np.fft.fft2(r.normal(size=(n, n)))
    ky = np.fft.fftfreq(n)[:, None]; kx = np.fft.fftfreq(n)[None, :]; k = np.sqrt(kx * kx + ky * ky) + 1e-9
    m = ((k >= 1.0 / hi) & (k <= 1.0 / lo)).astype(float)
    x = np.real(np.fft.ifft2(f * m)); return (x - x.mean()) / (x.std() + 1e-9)

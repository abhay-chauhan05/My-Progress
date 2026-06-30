"""
CMOD5.N geophysical model function (GMF)
========================================

CMOD5.N relates the C-band VV-polarised normalised radar cross-section
(NRCS / sigma-naught) measured by Sentinel-1 to the 10 m *neutral* ocean wind,
given the radar incidence angle and the wind direction relative to the radar
azimuth look direction.

* ``cmod5n_forward`` : wind speed, relative direction, incidence -> sigma0
* ``cmod5n_inverse`` : sigma0, relative direction, incidence -> wind speed

The CMOD family was developed at ECMWF / KNMI for scatterometer and SAR wind
retrieval.  This vectorised NumPy port follows the reference implementation
distributed with the open-source *openwind* project (NERSC), itself a
translation of the KNMI Fortran-90 routine.

References
----------
A. Stoffelen & S. de Haan (CMOD5 prototype, KNMI 2001);
H. Hersbach (ECMWF 2002, revision);
A. Verhoef (KNMI 2008, neutral-wind CMOD5.N);
K.-F. Dagestad (NERSC 2011, vectorised Python).
See https://scatterometer.knmi.nl/cmod5/

The numerical coefficients are part of the published geophysical model and are
in the public domain.  Implementation re-expressed for clarity here.
"""
from __future__ import annotations

import warnings

import numpy as np

# Wind retrieval over land produces overflow in the exponentials; that is fine,
# those pixels are masked out downstream.
warnings.simplefilter("ignore", RuntimeWarning)

# Empirical CMOD5.N coefficients (index 0 is padding to keep the 1-based
# indexing used in the original Fortran reference).
_C = np.array(
    [
        0.0,
        -0.6878, -0.7957, 0.3380, -0.1728, 0.0000, 0.0040, 0.1103, 0.0159,
        6.7329, 2.7713, -2.2885, 0.4971, -0.7250, 0.0450,
        0.0066, 0.3222, 0.0120, 22.7000, 2.0813, 3.0000, 8.3659,
        -3.3428, 1.3236, 6.2437, 2.3893, 0.3249, 4.1590, 1.6930,
    ]
)

_DTOR = 57.29577951
_THETM = 40.0
_THETHR = 25.0
_ZPOW = 1.6


def cmod5n_forward(v, phi, theta):
    """Forward CMOD5.N model.

    Parameters
    ----------
    v : array_like
        10 m neutral wind speed [m/s], must be >= 0.
    phi : array_like
        Angle between the radar azimuth look direction and the wind
        direction [deg].
    theta : array_like
        Radar incidence angle [deg].

    Returns
    -------
    numpy.ndarray
        Normalised radar cross-section (sigma0) in **linear** units.
    """
    v = np.asarray(v, dtype=float)
    phi = np.asarray(phi, dtype=float)
    theta = np.asarray(theta, dtype=float)

    C = _C
    y0 = C[19]
    pn = C[20]
    a = C[19] - (C[19] - 1.0) / C[20]
    b = 1.0 / (C[20] * (C[19] - 1.0) ** (pn - 1.0))

    # Angles.
    fi = phi / _DTOR
    csfi = np.cos(fi)
    cs2fi = 2.0 * csfi * csfi - 1.0

    x = (theta - _THETM) / _THETHR
    xx = x * x

    # B0: function of wind speed and incidence angle.
    a0 = C[1] + C[2] * x + C[3] * xx + C[4] * x * xx
    a1 = C[5] + C[6] * x
    a2 = C[7] + C[8] * x

    gam = C[9] + C[10] * x + C[11] * xx
    s0 = C[12] + C[13] * x

    s = a2 * v
    s_vec = np.atleast_1d(s).astype(float).copy()
    s0_arr = np.broadcast_to(np.atleast_1d(s0), s_vec.shape)
    below = s_vec < s0_arr
    s_vec = np.where(below, s0_arr, s_vec)

    a3 = 1.0 / (1.0 + np.exp(-s_vec))
    a3 = np.where(
        below,
        a3 * (np.atleast_1d(s) / s0_arr) ** (s0_arr * (1.0 - a3)),
        a3,
    )
    b0 = (a3 ** gam) * 10.0 ** (a0 + a1 * v)

    # B1: function of wind speed and incidence angle.
    b1 = C[15] * v * (0.5 + x - np.tanh(4.0 * (x + C[16] + C[17] * v)))
    b1 = C[14] * (1.0 + x) - b1
    b1 = b1 / (np.exp(0.34 * (v - C[18])) + 1.0)

    # B2: function of wind speed and incidence angle.
    v0 = C[21] + C[22] * x + C[23] * xx
    d1 = C[24] + C[25] * x + C[26] * xx
    d2 = C[27] + C[28] * x

    v2 = v / v0 + 1.0
    v2 = np.atleast_1d(v2).astype(float)
    lt = v2 < y0
    v2 = np.where(lt, a + b * (v2 - 1.0) ** pn, v2)
    b2 = (-d1 + d2 * v2) * np.exp(-v2)

    sigma0 = b0 * (1.0 + b1 * csfi + b2 * cs2fi) ** _ZPOW
    return sigma0.reshape(np.broadcast(v, phi, theta).shape)


def cmod5n_inverse(sigma0_obs, phi, incidence, iterations: int = 10):
    """Invert CMOD5.N to retrieve wind speed from observed sigma0.

    Uses a bisection-style iteration around the monotonic forward model.

    Parameters
    ----------
    sigma0_obs : array_like
        Observed NRCS [linear units].
    phi : array_like
        Wind direction relative to radar azimuth look [deg].
    incidence : array_like
        Incidence angle [deg].
    iterations : int
        Number of bisection refinements (10 -> ~0.02 m/s resolution).

    Returns
    -------
    numpy.ndarray
        Retrieved 10 m neutral wind speed [m/s].
    """
    sigma0_obs = np.asarray(sigma0_obs, dtype=float)
    phi = np.broadcast_to(np.asarray(phi, dtype=float), sigma0_obs.shape)
    incidence = np.broadcast_to(np.asarray(incidence, dtype=float), sigma0_obs.shape)

    v = 10.0 * np.ones(sigma0_obs.shape, dtype=float)
    step = 10.0

    for _ in range(1, max(2, iterations)):
        sigma0_calc = cmod5n_forward(v, phi, incidence)
        ind = (sigma0_calc - sigma0_obs) > 0
        v = v + step
        v[ind] = v[ind] - 2.0 * step
        step = step / 2.0

    return np.clip(v, 0.0, 50.0)

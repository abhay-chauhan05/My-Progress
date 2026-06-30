"""Tests for the CMOD5.N geophysical model function."""
import numpy as np

from windfield.cmod5n import cmod5n_forward, cmod5n_inverse


def test_forward_returns_positive_sigma0():
    v = np.array([5.0, 10.0, 15.0])
    phi = np.array([0.0, 45.0, 90.0])
    theta = np.array([35.0, 35.0, 35.0])
    s0 = cmod5n_forward(v, phi, theta)
    assert s0.shape == v.shape
    assert np.all(s0 > 0)


def test_forward_monotonic_in_wind_speed():
    # Upwind backscatter increases with wind speed in C-band VV.
    speeds = np.linspace(3, 20, 18)
    phi = np.zeros_like(speeds)
    theta = np.full_like(speeds, 35.0)
    s0 = cmod5n_forward(speeds, phi, theta)
    assert np.all(np.diff(s0) > 0)


def test_inverse_recovers_forward():
    truth = np.array([4.0, 7.5, 11.0, 16.0])
    phi = np.array([10.0, 120.0, 200.0, 300.0])
    theta = np.array([32.0, 36.0, 40.0, 44.0])
    s0 = cmod5n_forward(truth, phi, theta)
    retrieved = cmod5n_inverse(s0, phi, theta, iterations=16)
    # Bisection from a 10 m/s guess should converge to within ~0.1 m/s.
    assert np.allclose(retrieved, truth, atol=0.1)


def test_scalar_inputs():
    s0 = cmod5n_forward(8.0, 30.0, 38.0)
    assert np.ndim(s0) == 0 or s0.size == 1

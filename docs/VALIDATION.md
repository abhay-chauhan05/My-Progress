# Validation Results

## Methodology

The retrieval skill is quantified with a **closed-loop synthetic round-trip**:

1. A spatially-varying "true" 10 m wind field (speed + direction) is drawn for
   the area/date. Direction follows a monsoon-driven prevailing bearing; speed
   varies at mesoscale (~50 km).
2. The CMOD5.N **forward** model converts the truth wind, the modelled
   incidence-angle ramp (30 deg near-range -> 46 deg far-range, as for
   Sentinel-1 IW) and the radar look geometry into VV sigma0.
3. Wind-roll texture (oriented with the local wind) and multiplicative,
   multi-look speckle are imprinted to emulate a real SAR scene.
4. The **full retrieval** is run: structure-tensor wind-direction estimation
   followed by CMOD5.N **inversion** for wind speed.
5. Retrieved fields are compared against the stored truth.

Because the truth wind is known exactly, this isolates and measures the error
of each algorithmic stage. Against real acquisitions the identical statistics
would be computed versus ERA5 reanalysis, ASCAT scatterometer winds, or
in-situ buoy observations (data hooks are provided in
`windfield/sar_source.py::CopernicusSource`).

Reproduce with:

```bash
python -m windfield.validation
```

## Results (grid spacing 3 km)

| Region / Date | N points | Speed bias (m/s) | Speed RMSE (m/s) | Speed corr | Dir RMSE (deg) | Dir within 30 deg (%) |
|---|---:|---:|---:|---:|---:|---:|
| Tamil Nadu, 2024-01-15 (NE monsoon) | 5251 | -0.01 | 0.47 | 0.988 | 29.8 | 75.2 |
| Tamil Nadu, 2024-07-10 (SW monsoon) | 5251 | -0.01 | 0.50 | 0.987 | 31.4 | 77.6 |
| Gujarat, 2024-02-20 (NE monsoon) | 10584 | -0.01 | 0.54 | 0.985 | 27.6 | 79.1 |
| Gujarat, 2024-06-25 (SW monsoon) | 10584 | -0.01 | 0.56 | 0.986 | 33.3 | 78.7 |

## Interpretation

* **Wind speed (CMOD5.N inversion)** is the strong link in the chain: near-zero
  bias, RMSE around 0.5 m/s and correlation ~0.99 against truth. This is in line
  with published C-band SAR wind-speed performance once the wind direction is
  known.
* **Wind direction** is the harder problem. The dependency-free structure-tensor
  retriever reaches ~30 deg RMSE with ~77 % of estimates within 30 deg, and is
  subject to the well-known 180 deg streak ambiguity (resolved here with a
  meteorological prior). This is precisely the gap that the optional ResNet
  retriever (`windfield/ml/resnet_direction.py`, after training on labelled
  patches) is designed to close, following the referenced literature.
* Direction error propagates into speed error through the CMOD5.N geometry; the
  end-to-end speed RMSE therefore remains the headline accuracy metric for
  wind-farm resource screening.

## Notes for real-data validation

When `CopernicusSource` is enabled (credentials + `requirements-sentinel.txt`),
replace the synthetic truth with co-located reference winds and recompute the
same table. The harness in `windfield/validation.py` is structured so only the
"truth" source needs to be swapped.

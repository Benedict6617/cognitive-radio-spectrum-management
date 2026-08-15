# Architecture

## Overview

SpectrumSense is a modular monolith (one deployable FastAPI service) that
simulates the decision-logic stack of a cognitive radio spectrum-management
system, structured so each concern is independently testable and so a real
hardware backend can be substituted later without touching the algorithms.

## Layers

1. **Spectrum sensing (simulated)** — `app/services/spectrum_sensor.py`
   generates synthetic wideband energy-detection sweeps per node: a noise
   floor, a per-channel "true" occupancy-probability pattern (modeling
   incumbent/primary-user activity), and per-node measurement noise. This
   is the layer a real deployment would replace with an actual SDR energy
   detector or feature-detector front end.

2. **Cooperative spectrum sensing** — `app/services/cooperative_sensing.py`
   implements a reliability-weighted soft-fusion rule: each node's report
   is weighted by a `reliability_weight` (e.g. derived from historical
   node accuracy or link quality), and a channel is declared occupied if
   the weighted vote clears a configurable threshold. This mitigates the
   classic single-node cognitive-radio problems of fading and the hidden
   primary-user problem.

3. **Protected-band registry** — `app/services/protected_bands.py` loads a
   list of frequency ranges that must never be allocated to. **Sample data
   only** — see `docs/REGULATORY_NOTES.md`.

4. **Channel allocation** — `app/services/channel_allocator.py` combines
   the fused sensing decision with the protected-band registry to pick the
   best available channel (or report full per-channel status), always
   excluding protected and occupied channels.

5. **Power control** — `app/services/power_control.py` implements the
   classical Foschini–Miljanic distributed power-control iteration:

   ```
   p_i(t+1) = p_i(t) * (target_SINR / achieved_SINR_i(t))
   ```

   which is known to converge to the component-wise minimum feasible power
   vector when the system is feasible, minimizing aggregate transmit power
   (and therefore aggregate interference) system-wide.

6. **Predictive usage analytics** — `app/services/usage_forecaster.py`
   implements a lightweight, dependency-free self-attention forecaster:
   the recent observation window is a query, historical windows are keys,
   and their known continuations are values; scaled dot-product attention
   blends the most similar historical continuations into the forecast.
   This mirrors how a transformer's attention mechanism weighs relevant
   history, without requiring a deep-learning framework, so it fits a
   small lab's toolchain and trains instantly on modest data.

7. **SDR interface (mock)** — `app/services/sdr_interface.py` defines the
   abstract contract (`SDRInterface`) a real hardware backend would
   implement, and a `MockSDR` that simulates the same state transitions in
   memory. No code in this repository transmits or receives real RF.

8. **API** — `app/routers/` exposes each layer as REST endpoints for
   scans/fusion, node registry, allocation, power control, and forecasts.

## Data flow

```
per-node sensing (simulated) ──▶ cooperative fusion ──▶ channel allocator ──▶ SDR interface (mock)
                                                              ▲
                          protected-band registry ────────────┘

historical scan log ──▶ usage forecaster (attention over analogs) ──▶ /forecast API
```

## Extending this project

- **Real hardware**: implement `SDRInterface` against GNU Radio/UHD/
  SoapySDR and inject it in place of `MockSDR`; sensing/fusion/allocation/
  power-control code is unchanged.
- **Authoritative regulatory data**: replace `data/sample/protected_bands.csv`
  with a real, currently maintained allocation table for your jurisdiction
  and equipment authorization, and re-verify before any real transmission.
- **Learned forecaster**: swap `TransformerLiteForecaster` for a trained
  parametric model (e.g. a small PyTorch transformer) behind the same
  `fit`/`predict` interface if you have enough historical data to justify it.
- **Distributed deployment**: today all nodes are simulated centrally for
  simplicity; a real deployment would run a lightweight sensing agent per
  physical node reporting to the fusion center over a message bus.

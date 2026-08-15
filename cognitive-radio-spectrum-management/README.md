# SpectrumSense — Cognitive Radio Spectrum Management Simulator

SpectrumSense is a software reference implementation of a cognitive radio
spectrum-management system: it simulates wideband RF spectrum scanning
across a network of distributed sensing nodes, performs cooperative
(multi-node) spectrum sensing, allocates channels to a software-defined
radio (SDR) array while keeping a configurable set of protected bands
clear, runs a closed-loop power-control algorithm to limit inter-cell
interference, and forecasts channel occupancy with a lightweight
attention-based time-series model.

> 📝 **Note to self before publishing:** add your own project description /
> screenshots here when you push this to GitHub. The section below is a
> starting template you can replace.

## ⚠️ Important scope note

This is a **simulation and decision-logic framework**, not a hardware
driver. `app/services/sdr_interface.py` defines an abstract SDR control
interface with a `MockSDR` implementation that operates on simulated
spectrum data — there is no code here that transmits, receives, or
otherwise drives physical RF hardware. The protected-band registry ships
with a small set of illustrative, publicly-known band allocations for
demonstration purposes (e.g. generic public-safety and aeronautical radar
ranges) — **it is not a substitute for an authoritative regulatory
database** (in the U.S., consult the FCC Table of Frequency Allocations;
elsewhere, your national spectrum regulator) and must not be relied on for
real-world spectrum-access decisions. Anyone connecting this decision
logic to real SDR hardware is responsible for independently verifying
regulatory compliance (e.g. FCC Part 15/90/97, ETSI EN 301 598, or your
local equivalent) before transmitting.

## What it does

- **Wideband spectrum scanning (simulated):** generates synthetic
  energy-detection sweeps across a configurable frequency range and channel
  raster, modeling primary-user activity, noise floor, and fading.
- **Cooperative spectrum sensing:** a fusion center combines reports from
  multiple distributed sensing nodes using weighted (reliability-scored)
  voting to reach a more robust occupied/unoccupied decision than any
  single node, per the OR-rule / weighted-fusion patterns used in the
  cognitive radio literature.
- **Protected-band avoidance:** a channel allocator that never assigns a
  channel overlapping a registered protected band (public-safety,
  aeronautical radar, etc. — sample data only, see scope note above), and
  otherwise picks the least-congested unoccupied channel.
- **Dynamic power control:** a Foschini–Miljanic-style iterative
  power-control loop that lets each simulated link converge on the minimum
  transmit power needed to hit its target signal-to-interference ratio,
  reducing aggregate inter-cell interference.
- **Predictive usage analytics:** a compact, dependency-light self-attention
  (transformer-style) time-series forecaster — implemented in NumPy so it
  runs anywhere without a deep-learning framework — that predicts near-term
  channel occupancy from historical sensing data.
- **REST API** (FastAPI) exposing scans, node reports, allocations, power-
  control state, and forecasts, with realistic simulated sample data
  included so the system is explorable immediately.

## Why this fits a small business / lab

- Runs entirely as software simulation on a laptop — no SDR hardware or
  RF test license required to explore the algorithms.
- The `SDRInterface` abstraction is the intended integration point for a
  real hardware backend (e.g. a GNU Radio / UHD / SoapySDR driver) later,
  without changing the sensing, fusion, allocation, or power-control logic.
- Small, auditable codebase suitable for a research group, telecom
  consultancy, or spectrum-engineering small business to extend.

## Architecture

```
 Distributed sensing nodes (simulated)
        |
        v
+-------------------+     +----------------------+     +----------------------+
| Spectrum Sensor    |---->| Cooperative Fusion    |---->| Channel Allocator     |
| (energy detection)  |     | Center (weighted vote) |     | (avoids protected +   |
+-------------------+     +----------------------+     |  occupied channels)   |
                                                          +----------+-----------+
                                                                     |
                                                                     v
+-------------------+     +----------------------+     +----------------------+
| Usage Forecaster    |<----| Historical Scan Log   |     | Power Control Loop    |
| (NumPy self-attn.)  |     +----------------------+     | (Foschini-Miljanic)   |
+-------------------+                                    +----------------------+
                                                                     |
                                                                     v
                                                          +----------------------+
                                                          | SDR Interface (mock)  |
                                                          +----------------------+
```

Full details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
Regulatory scope notes: [`docs/REGULATORY_NOTES.md`](docs/REGULATORY_NOTES.md)
API reference: [`docs/API.md`](docs/API.md)

## Project layout

```
cognitive-radio-spectrum-management/
├── app/
│   ├── main.py                     # FastAPI app entrypoint
│   ├── config.py                    # environment-based settings
│   ├── models.py                     # Pydantic domain models
│   ├── routers/                      # API route modules
│   └── services/
│       ├── spectrum_sensor.py         # simulated wideband scanning
│       ├── protected_bands.py         # sample regulatory band registry
│       ├── cooperative_sensing.py     # multi-node fusion center
│       ├── channel_allocator.py       # dynamic channel selection
│       ├── power_control.py           # closed-loop power control
│       ├── usage_forecaster.py        # NumPy self-attention forecaster
│       └── sdr_interface.py           # abstract SDR interface + mock backend
├── data/sample/                       # realistic, synthetic sample data (CSV)
├── scripts/                            # data generation / training / demo scripts
├── tests/                              # pytest unit tests
└── docs/                               # architecture, API, regulatory notes
```

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Generate a realistic synthetic multi-node scan history
python scripts/generate_sample_data.py

# 2. Train the occupancy forecaster on the sample scan history
python scripts/train_forecaster.py

# 3. Run a one-shot cooperative sensing -> allocation -> power-control demo
python scripts/simulate_spectrum_scan.py

# 4. Run the API
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for the interactive API explorer.

### Docker

```bash
docker compose up --build
```

## Sample data

`data/sample/` ships with fully synthetic data so the system is usable
immediately:

| File                     | Contents                                                |
|---------------------------|-----------------------------------------------------------|
| `node_registry.csv`        | 8 distributed sensing nodes with location and reliability |
| `protected_bands.csv`      | Illustrative protected-band registry (sample only)         |
| `spectrum_scans.csv`       | 14 days of per-node, per-channel occupancy sensing reports |
| `power_control_log.csv`    | Sample power-control convergence log for 12 simulated links|

No real classified, restricted, or export-controlled frequency data is
included anywhere in this repository.

## Testing

```bash
pytest -q
```

## License

MIT — see [`LICENSE`](LICENSE).

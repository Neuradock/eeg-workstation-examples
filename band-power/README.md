# EEG Band Power Analysis

Jupyter notebook tutorial for computing and visualizing canonical EEG frequency-band power on NeuraDock dry-electrode recordings.

---

## Overview

This notebook performs a complete **band-power analysis** pipeline:

1. **Load** resting-state and task-state EEG data.
2. **Preprocess** — apply a 50 Hz notch filter and a 0.5–100 Hz band-pass filter.
3. **Compute Welch PSD** for every channel (2 s Hamming windows, 50 % overlap).
4. **Extract band power** — absolute (μV²) and relative (%) for Delta, Theta, Alpha, Beta, and Gamma.
5. **Visualize**:
   - PSD spectrum with band shading
   - Absolute & relative band-power bar charts (all 7 channels)
   - Time–frequency spectrogram
6. **Compare** resting vs. task states to reveal **Alpha ERD** (Event-Related Desynchronization).

---

## Files Required

| File | Description |
|------|-------------|
| `band_power.ipynb` | This tutorial notebook |
| `Neuradock_library.py` | Core helper (`text2data_bluetooth`) |
| `rest_20251024160452_2m12s.txt` | Resting-state paradigm data (~2 min 13 s, 7 ch, 250 Hz) |
| `task_20251024160748_2m33s.txt` | Task-state paradigm data (~2 min 34 s, 7 ch, 250 Hz) |

---

## Environment

- **Python**: 3.9 – 3.11
- **Dependencies**: `numpy`, `scipy`, `matplotlib`

```bash
pip install numpy scipy matplotlib
```

---

## Quick Start

```bash
jupyter notebook band_power.ipynb
```

Run all cells sequentially. The notebook is self-contained and produces 3 publication-quality figures:

1. **Spectrum + Band Power Bars** — mean PSD with canonical bands highlighted; absolute & relative power per channel.
2. **Spectrogram** — time–frequency evolution of Channel 1 (occipital) during rest.
3. **Rest vs. Task Comparison** — overlaid PSD curves, mean band-power bars, and per-channel Alpha ERD (%).

---

## Band Definitions

| Band | Frequency (Hz) | Typical Association |
|------|----------------|---------------------|
| **Delta** | 0.5 – 4 | Deep sleep, unconsciousness |
| **Theta** | 4 – 8 | Drowsiness, meditation |
| **Alpha** | 8 – 13 | Relaxed wakefulness, eyes-closed |
| **Beta**  | 13 – 30 | Active thinking, alert focus |
| **Gamma** | 30 – 100 | High-level cognitive processing |

---

## Expected Output

- **Resting state** typically shows prominent **Alpha** power in occipital channels (Ch 1, 6, 7).
- **Task state** typically shows **Alpha ERD** (power drop) and slight **Beta/Gamma** increase.
- Power is reported both as:
  - **Absolute** (μV²) — useful for examining raw energy
  - **Relative** (%) — useful for cross-session and cross-subject comparison

---

## Notes

- The analysis intentionally uses **cleaned** preprocessed data (notch + band-pass) to avoid 50 Hz line-noise contamination.
- Welch parameters: `nperseg = 500` (2 s), `noverlap = 250` (50 %), Hann window.
- Band power is computed by numerical integration (`np.trapezoid`) of the PSD within each frequency boundary.
- If you want to adapt this to your own recordings, simply replace the two `.txt` file paths in **Cell 2**.

# Eyes-Open vs. Eyes-Closed (Alpha Blocking) Demo

Standalone Jupyter notebook demonstrating Alpha-wave analysis on NeuraDock dry-electrode EEG data.

---

## What It Does

This notebook runs a complete **Eyes-Open / Eyes-Closed (Alpha Blocking)** analysis pipeline:

1. **Load** raw Bluetooth-format EEG text data.
2. **Inspect** all 7 channels in the time domain.
3. **Quality check & clean** the signal (remove 50 Hz, EMG, and outlier artifacts).
4. **Alpha analysis** on the cleaned data:
   - Band-pass filter to 8–13 Hz.
   - Hilbert envelope to track Alpha amplitude over time.
   - Automatic thresholding (50th percentile) to separate **Eyes-Closed** (high Alpha) from **Eyes-Open** (low Alpha) segments.
   - 5-panel comprehensive figure: full trace, spectrogram, zoomed Alpha wave, zoomed resting wave, and 7-channel SNR bars.
5. **Quantitative comparison**:
   - Average Welch PSD for EC vs. EO periods.
   - Envelope segmentation overlay plot.
   - Multi-channel Alpha power (8–13 Hz) bar chart.

---

## Files Required

| File | Description |
|------|-------------|
| `eyes_open_closed_demo.ipynb` | This demo notebook |
| `Neuradock_library.py` | Core helper functions (`text2data_bluetooth`, `eeg_quality_check`, `clean_eeg_data`, `analyze_alpha_and_plot_eeg_group`, etc.) |

---

## Environment

- **Python**: 3.9 / 3.10 / 3.11
- **Dependencies**: `numpy`, `scipy`, `matplotlib`, `pandas`, `seaborn`

Install via:

```bash
pip install numpy scipy matplotlib pandas seaborn
```

---

## Quick Start

```bash
jupyter notebook eyes_open_closed_demo.ipynb
```

Then run all cells sequentially. The notebook is self-contained — every step from data loading to final plots is included.

---

## Expected Output

- **Cleaned data retention**: ~66 % (original 52.8 s → cleaned ~34.8 s)
- **Alpha power ratio (EC / EO)**: typically **20–25×** on Channel 1
- **Figures**:
  - 7-channel raw trace
  - Raw vs. cleaned comparison
  - 5-panel Alpha analysis group chart
  - Envelope + PSD comparison (EC vs. EO)
  - 7-channel Alpha power bar chart

---

## Notes

- The analysis intentionally **uses cleaned data** for all Alpha calculations to avoid artifact contamination.
- Channel order follows the NeuraDock 10–20 mapping: `PO4, O2, T6, Oz, T5, O1, PO3`.
- If you want to adapt this notebook to your own recordings, simply replace `open_closed_eye2.txt` with your own Bluetooth-format `.txt` file.

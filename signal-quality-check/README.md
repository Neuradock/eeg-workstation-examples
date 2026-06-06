# EEG Signal Quality Detection — NeuraDock

A self-contained example that **automatically assesses the quality** of a NeuraDock EEG recording and **rejects the contaminated segments** before any downstream analysis.

All quality-control logic lives in `Neuradock_library.py`, so the notebook itself is only a handful of lines.

---

## Files

| File | Description |
| :--- | :--- |
| `signal_quality_check.ipynb` | The walkthrough notebook (load → detect → summarise → clean → compare). |
| `Neuradock_library.py` | NeuraDock helper library (`text2data_bluetooth`, `eeg_quality_check`, `clean_eeg_data`, `visualize_cleaning_comparison`). |
| `example_data_bluetooth.txt` | Sample Bluetooth recording (7 channels, 250 Hz, ~9 s). |

---

## What it checks

The recording is split into **1-second segments** (250 samples). For every channel and segment, three metrics are computed and compared against hardware-tuned thresholds:

| Metric | Band / Rule | Threshold | Catches |
| :--- | :--- | :--- | :--- |
| **50 Hz power** | 49–51 Hz | `10` | Power-line interference |
| **EMG power** | 20–40 Hz | `20` | Muscle activity (clench, movement) |
| **Outlier count** | \|x\| ≥ 100 µV | `2` | Electrode pops, motion, saturation |

Channels that are bad for more than **40 %** of the recording are flagged as **bad channels**; time segments that are bad on the *good* channels are cut out.

---

## Requirements

```bash
pip install numpy scipy matplotlib seaborn pandas
```

- **Python**: 3.9 / 3.10
- **Sampling rate**: 250 Hz (NeuraDock default)

---

## Run it

```bash
jupyter notebook signal_quality_check.ipynb
```

Then run the cells top to bottom. The notebook will:

1. Load `example_data_bluetooth.txt` → `(7, N)` array via `text2data_bluetooth`.
2. Call `eeg_quality_check(...)` to compute the three metric matrices and draw the **time-domain diagnostic** (bad segments shaded: red = 50 Hz, blue = EMG, gray = outliers) and three **heatmaps**.
3. Print a per-channel **bad-segment ratio** table.
4. Call `clean_eeg_data(...)` to drop contaminated segments and report the retention rate.
5. Call `visualize_cleaning_comparison(...)` for a before/after plot.

---

## Key parameters

| Parameter | Where | Default | Description |
| :--- | :--- | :--- | :--- |
| `thresh` | notebook | `[10, 20, 2]` | `[50Hz, EMG, Outlier]` thresholds — must match the value used inside `eeg_quality_check`. |
| `seg_len` | `clean_eeg_data` | `250` | Segment length in samples (1 s @ 250 Hz). |
| `bad_ch_ratio` | `clean_eeg_data` | `0.4` | A channel bad for more than this fraction of time is dropped. |

---

## Tips

- Tune `thresh` to your environment — noisier rooms need higher 50 Hz / EMG limits. Keep the notebook value identical to the library's internal value.
- Swap `example_data_bluetooth.txt` for a longer recording (e.g. `rest_*.txt`) to make the heatmaps more informative.
- For spectral analysis of the cleaned signal, see the sibling `../psd-analysis` example.

# EEG Power Spectral Density (PSD) — NeuraDock

A self-contained example that estimates and visualises the **power spectral density** of a NeuraDock EEG recording using **Welch's method**, then reads off the canonical EEG frequency bands.

The PSD is the foundation for band-power, SSVEP, alpha-rhythm and most other spectral analyses — it tells you *how much signal power sits at each frequency*.

A clean spectrum requires clean data, so the pipeline screens the recording and **drops the bad-quality segments before** computing the PSD:

> **load → quality check → drop bad segments → preprocess → PSD**

---

## Files

| File | Description |
| :--- | :--- |
| `psd_analysis.ipynb` | The walkthrough notebook (load → quality check & clean → preprocess → Welch PSD → plot → band power → one-call analysis). |
| `Neuradock_library.py` | NeuraDock helper library (`text2data_bluetooth`, `eeg_quality_check`, `clean_eeg_data`, `analyze_alpha_and_plot_eeg_group`). |
| `rest_20251024160452_2m12s.txt` | Resting-state recording (7 channels, 250 Hz, ~132 s) with a clear occipital alpha peak. |

---

## Frequency bands

| Band | Frequency (Hz) | Typical association |
| :--- | :--- | :--- |
| **Delta** | 0.5 – 4 | Deep sleep |
| **Theta** | 4 – 8 | Drowsiness, meditation |
| **Alpha** | 8 – 13 | Relaxed, eyes-closed (strong over occipital channels) |
| **Beta** | 13 – 30 | Active thinking, focus |
| **Gamma** | 30 – 100 | High-level cognitive processing |

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
jupyter notebook psd_analysis.ipynb
```

Then run the cells top to bottom. The notebook will:

1. Load `rest_20251024160452_2m12s.txt` → `(7, N)` array via `text2data_bluetooth`.
2. **Quality check & clean**: `eeg_quality_check(...)` scores each 1-second segment (50 Hz / EMG / outliers) and `clean_eeg_data(...)` removes the contaminated segments — so artefact power never enters the spectrum.
3. **Preprocess** the cleaned signal: 50 Hz notch + 0.5–100 Hz band-pass (zero-phase `filtfilt`).
4. Compute a **Welch PSD** per channel (2 s Hann window, 50 % overlap → 0.5 Hz resolution).
5. Plot the spectra (linear + log/dB) over 0–45 Hz with the alpha band highlighted.
6. Integrate the PSD into **relative band power** per channel and chart it.
7. Call `analyze_alpha_and_plot_eeg_group(...)` for a one-shot figure: time domain + spectrogram + alpha/resting zoom + per-channel alpha-band SNR.

---

## Key parameters

| Parameter | Where | Default | Description |
| :--- | :--- | :--- | :--- |
| `fs` | notebook | `250` | Sampling rate (Hz). |
| `thresh` | `clean_eeg_data` | `[10, 20, 2]` | `[50Hz, EMG, Outlier]` rejection thresholds — must match `eeg_quality_check`. |
| `bad_ch_ratio` | `clean_eeg_data` | `0.4` | A channel bad for more than this fraction of time is flagged bad. |
| `nperseg` | Welch | `fs * 2` | Window length — longer = finer resolution, noisier estimate. |
| `noverlap` | Welch | `fs` | 50 % overlap between windows. |
| `fmax` | plot | `45` | Upper frequency shown (most EEG rhythms live below this). |
| `show_channel` | `analyze_alpha_and_plot_eeg_group` | `3` | Main channel for the time-domain / spectrogram panels. |

---

## Tips

- **Quality first.** A few seconds of 50 Hz pickup or muscle noise can dominate the PSD, so the recording is screened and cleaned before the spectrum is computed. `clean_eeg_data` concatenates the surviving segments, leaving small discontinuities at the splice points — negligible for Welch PSD, which averages many short windows.
- **Alpha** is strongest over occipital channels and rises when the eyes are closed — compare a `rest` (eyes-closed) recording against a `task` recording to see the difference.
- Use **relative** band power when comparing across channels/sessions; absolute power depends on electrode impedance and gain.
- For the quality-check / cleaning step in full detail, see the sibling `../signal-quality-check` example.

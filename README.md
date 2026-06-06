# NeuraDock EEG Workstation — Examples

A collection of complete, runnable **EEG example workflows** for the **NeuraDock EEG Workstation** — a 7-channel dry-electrode EEG development kit for researchers, developers, and makers working with brain signals.

Each example lives in its own folder with a dedicated `README.md`, the helper library or scripts it needs, and a Jupyter notebook or Python program. The examples span the full stack: **signal-quality control, spectral analysis, evoked-potential BCI paradigms (SSVEP / c-VEP), real-time event marking, and advanced research demos.**

---

## 📂 Examples

| Example | Directory | What it does | Type |
|---|---|---|---|
| **Signal Quality Check** | [`signal-quality-check/`](signal-quality-check/) | Score every 1-second segment for 50 Hz / EMG / outlier noise, flag bad channels, and remove contaminated segments. | Notebook (offline) |
| **PSD Analysis** | [`psd-analysis/`](psd-analysis/) | Quality-clean a recording, then estimate the power spectral density (Welch) and relative band power per channel. | Notebook (offline) |
| **Band Power** | [`band-power/`](band-power/) | Compute Delta–Gamma band power and compare resting vs. task states to reveal **Alpha ERD**. | Notebook (offline) |
| **Eyes Open / Closed** | [`eyes-open-closed/`](eyes-open-closed/) | Classic **Alpha-blocking** demo — detect eyes-closed vs. eyes-open from the 8–13 Hz Alpha envelope. | Notebook (offline) |
| **SSVEP** | [`ssvep/`](ssvep/) | Frequency-tagged flicker stimulation (PsychoPy) + offline SSVEP frequency-domain analysis. | Experiment (live) |
| **c-VEP Speller** | [`neuradock_cvep/`](neuradock_cvep/) | Code-modulated VEP speller: m-sequence calibration → online 4-target decoding (TTCA). | Experiment (live) |
| **Real-Time Marker** | [`marker/`](marker/) | Stream EEG over TCP and inject event markers into the live data for paradigm synchronization. | Library (live) |
| **Visual Reconstruction** | [`Visual-reconstruction/`](Visual-reconstruction/) | Reconstruct viewed images from 7-channel occipital EEG using guided diffusion (links to full project repo). | Research demo |

---

## 📥 Getting the Data

The example recordings (`.txt` EEG files) are **not stored in this repository**. They live in a separate data repository:

### 👉 https://github.com/Neuradock/eeg-workstation-data

Download the file(s) an example needs and place them **inside that example's folder** (next to its notebook), then run the notebook. Each notebook loads its data by filename from the current working directory.

| Example | Required data file(s) |
|---|---|
| `signal-quality-check/` | `example_data_bluetooth.txt` |
| `psd-analysis/` | `rest_20251024160452_2m12s.txt` |
| `band-power/` | `rest_20251024160452_2m12s.txt`, `task_20251024160748_2m33s.txt` |
| `eyes-open-closed/` | `open_closed_eye2.txt` |
| `ssvep/`, `neuradock_cvep/`, `marker/` | *None* — these record their own data live from the device. |
| `Visual-reconstruction/` | See the [project repository](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock). |

> **Tip:** clone the data repo once, then copy the file you need into the example folder:
> ```bash
> git clone https://github.com/Neuradock/eeg-workstation-data
> cp eeg-workstation-data/rest_20251024160452_2m12s.txt psd-analysis/
> ```

---

## 🧠 Hardware & Data Format

- **Device**: NeuraDock 7-channel dry-electrode EEG.
- **Sampling rate**: 250 Hz.
- **Default channel layout**: `O1, O2, Oz, PO3, PO4, CP5, CP6` (occipital / parieto-occipital). Examples preserve this channel order unless otherwise stated.
- **Recording format**: comma-separated text. Bluetooth recordings pack 5 time-points per line × 7 channels; the helper `text2data_bluetooth()` parses a file into a `(7, N)` array. Live BCI scripts append a `marker\n` line at each stimulus onset for synchronization.

See [eeg-workstation-docs → Data Format](https://github.com/Neuradock/eeg-workstation-docs/blob/main/data-format.md) for the full specification.

---

## ⚙️ Environment

- **Python**: 3.9 – 3.11
- **Core dependencies** (offline notebooks):

  ```bash
  pip install numpy scipy matplotlib pandas seaborn
  ```

- **Live experiments** (`ssvep/`, `neuradock_cvep/`) additionally need **PsychoPy** for stimulus presentation:

  ```bash
  pip install psychopy
  ```
  PsychoPy is most reliable on Python 3.9 / 3.10.

Each example's own `README.md` lists its exact requirements, parameters, and run instructions.

---

## 🚀 Quick Start (offline notebook example)

```bash
# 1. Get the data
git clone https://github.com/Neuradock/eeg-workstation-data

# 2. Place the needed file into the example folder
cp eeg-workstation-data/rest_20251024160452_2m12s.txt psd-analysis/

# 3. Launch the notebook
cd psd-analysis
jupyter notebook psd_analysis.ipynb
```

Run the cells top to bottom — every offline example is self-contained once its data file is present.

---

## 🔬 Example Details

### Signal Quality Check — [`signal-quality-check/`](signal-quality-check/)
Splits a recording into 1-second segments and scores each on **50 Hz line noise**, **EMG (20–40 Hz)**, and **outlier count** (|x| ≥ 100 µV). Produces time-domain and heatmap diagnostics, flags channels bad more than 40 % of the time, and splices out contaminated segments. The recommended **first step** before any analysis.

### PSD Analysis — [`psd-analysis/`](psd-analysis/)
Pipeline: **load → quality-check → drop bad segments → preprocess (notch + band-pass) → Welch PSD**. Plots linear and log spectra (0–45 Hz) with the Alpha band highlighted, derives relative band power per channel, and includes a one-call spectrogram + Alpha-SNR overview.

### Band Power — [`band-power/`](band-power/)
Computes absolute (µV²) and relative (%) power for Delta/Theta/Alpha/Beta/Gamma, and compares **resting vs. task** to surface **Alpha event-related desynchronization (ERD)**.

### Eyes Open / Closed — [`eyes-open-closed/`](eyes-open-closed/)
Tracks the 8–13 Hz Alpha envelope (Hilbert) and auto-thresholds it to separate eyes-closed (high Alpha) from eyes-open (low Alpha), with EC-vs-EO PSD comparison and per-channel Alpha power.

### SSVEP — [`ssvep/`](ssvep/)
Presents square-wave flicker stimuli via PsychoPy, writes event markers to the data stream, and runs an offline script that filters, epochs, and computes per-channel ERP + Welch PSD, exporting a multi-panel PDF. Requires a connected device.

### c-VEP Speller — [`neuradock_cvep/`](neuradock_cvep/)
A code-modulated VEP speller. All four targets share one 63-chip m-sequence, distinguished by circular shifts. `calibration.py` records the four templates; `online_test.py` presents 4 flickering targets and decodes each trial with the **TTCA** classifier (`ttca.py`). See the folder README for the full pipeline and file-based synchronization details. Requires a connected device.

### Real-Time Marker — [`marker/`](marker/)
`neuradock_marker.py` provides a TCP `DataStream` client and an `EEGThreadManager` that buffers samples in a background thread and appends an **event-marker column** to each sample — the synchronization backbone for SSVEP/cVEP/ERP paradigms.

### Visual Reconstruction — [`Visual-reconstruction/`](Visual-reconstruction/)
A pointer to a full research project that reconstructs viewed images from 7-channel occipital EEG using a guided-diffusion decoder (NeurIPS 2024 method adapted to NeuraDock). Source and instructions live in the [external repository](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock).

---

## 🔗 Related Repositories

| Repository | Purpose |
|---|---|
| [eeg-workstation](https://github.com/Neuradock/eeg-workstation) | Main project overview and repository navigation |
| [eeg-workstation-docs](https://github.com/Neuradock/eeg-workstation-docs) | Documentation, setup guides, data-format notes, tutorials |
| [eeg-workstation-software](https://github.com/Neuradock/eeg-workstation-software) | NeuraDock Recording Software releases and usage notes |
| [eeg-workstation-python](https://github.com/Neuradock/eeg-workstation-python) | Python tools, notebooks, and EEG data-reading examples |
| [eeg-workstation-agent](https://github.com/Neuradock/eeg-workstation-agent) | EEG Agent workflows, prompts, and analysis pipelines |
| [**eeg-workstation-data**](https://github.com/Neuradock/eeg-workstation-data) | **Sample EEG recordings used by the examples in this repository** |
| [eeg-workstation-hardware](https://github.com/Neuradock/eeg-workstation-hardware) | Hardware interface and port specifications |

---

## 📚 Related Documentation

| Document | Description |
|---|---|
| [Getting Started](https://github.com/Neuradock/eeg-workstation-docs/blob/main/getting-started.md) | First-time setup guide for NeuraDock EEG Workstation |
| [Software Installation](https://github.com/Neuradock/eeg-workstation-docs/blob/main/software-installation.md) | Software environment setup and installation guide |
| [Data Format](https://github.com/Neuradock/eeg-workstation-docs/blob/main/data-format.md) | EEG text file structure, channel layout, USB and Bluetooth formats |
| [USB Real-Time Streaming](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-streaming-usb.md) | Read real-time EEG data through the USB workflow |
| [Bluetooth Real-Time Streaming](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-streaming-bluetooth.md) | Read real-time EEG data through the Bluetooth workflow |
| [Read USB Text Files](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/read-txt-usb.md) | Parse EEG text files recorded from the USB workflow |
| [Read Bluetooth Text Files](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/read-txt-bluetooth.md) | Parse EEG text files recorded from the Bluetooth workflow |
| [Real-Time Marker Workflow](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-marker.md) | Stream EEG with event markers for experiment synchronization |
| [Signal Quality Check](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/signal-quality.md) | Evaluate basic EEG signal quality from recorded data |
| [SSVEP Workflow](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/ssvep.md) | Run visual stimulation and offline SSVEP analysis |
| [Troubleshooting](https://github.com/Neuradock/eeg-workstation-docs/blob/main/troubleshooting.md) | Common connection, recording, and software issues |

---

## 🌐 Links

- Website: [neuradock.com](https://neuradock.com)
- Crowd Supply: [NeuraDock EEG Workstation](https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation)
- YouTube: [@NeuraDock](https://www.youtube.com/@NeuraDock)
- Discord: NeuraDock Community

---

## 📝 Notes

- Offline notebooks are self-contained once their `.txt` data file (from [eeg-workstation-data](https://github.com/Neuradock/eeg-workstation-data)) is in place — no device required.
- Live experiments (`ssvep/`, `neuradock_cvep/`, `marker/`) require a connected NeuraDock device; set the device IP/port at the top of each script.
- This repository deliberately does **not** commit large datasets — keep recordings in the data repository and copy in only what an example needs.

---

## License

The license for this repository will be provided before public release. Unless otherwise stated, software code, documentation, sample data, and hardware interface materials may use different licenses across the NeuraDock GitHub organization.

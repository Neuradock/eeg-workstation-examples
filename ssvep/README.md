# SSVEP BCI Experiment — NeuraDock

This directory contains a complete **Steady-State Visual Evoked Potential (SSVEP)** brain-computer interface (BCI) pipeline based on the NeuraDock dry-electrode EEG device.

The pipeline covers **real-time stimulus presentation**, **data acquisition**, **offline preprocessing**, and **frequency-domain analysis**.

---

## File Overview

| File | Description |
| :--- | :--- |
| `ssvep.py` | **Visual Stimulation Program**. Uses PsychoPy to present square-wave flickering stimuli (white/black image alternation) at a target frequency. Writes event markers to `1.txt` for synchronization with EEG data. |
| `NeuraDock_socket.py` | **TCP Data Stream Client**. Connects to the NeuraDock device via TCP, receives real-time EEG data, and saves it as a comma-separated text file (`1.txt`). |
| `Neuradock_lib.py` | **Core Utility Library**. Provides data reading (`data_reader`), quality scoring (`EEG_quality_check`), visualization (`visualize_eeg_quality`), bandpass filtering (`butter_bandpass_filter`), automatic artifact rejection (`data_selecter`), and noise metrics calculation (`noise_calculation`). |
| `ssvep_result.py` | **Offline Analysis & Reporting**. Reads the recorded data and markers, performs filtering and epoch extraction, computes averaged ERP and Welch PSD per channel, and exports a multi-panel PDF figure. |
| `black.png` / `white.png` | Stimulus images used by `ssvep.py` for the OFF and ON states of the flicker. |

---

## System Requirements

- **Python**: 3.9 or 3.10 (PsychoPy compatibility)
- **NeuraDock Device**: Connected to the same LAN as the PC
- **Monitor Refresh Rate**: 60 Hz (default; update `SCREEN_REFRESH_RATE` in `ssvep.py` if different)

### Python Dependencies

```bash
pip install numpy scipy matplotlib psychopy
```

---

## Experiment Workflow

### Step 1 — Start Data Acquisition

Run `NeuraDock_socket.py` (or use the online streaming tutorial) to begin receiving EEG data from the NeuraDock device.

```bash
python NeuraDock_socket.py
```

This creates `1.txt` and continuously appends incoming EEG packets.

> **Tip**: Ensure the device IP and port in `NeuraDock_socket.py` match your NeuraDock configuration.

### Step 2 — Run the Visual Stimulation

Execute the SSVEP paradigm:

```bash
python ssvep.py
```

- Press **Space** to start.
- Fixate on the flickering square. The stimulus toggles between `white.png` and `black.png` at the configured frequency (default 4 Hz).
- Event markers (`marker\n`) are automatically written to `1.txt` at the onset of each stimulation block.
- Press **ESC** at any time to abort.

### Step 3 — Offline Analysis

After the experiment, run the analysis script:

```bash
python ssvep_result.py
```

It will:
1. Read `1.txt` and parse EEG data + markers.
2. Apply a 2–80 Hz bandpass filter.
3. Extract epochs around each marker.
4. Compute the averaged ERP and Welch PSD for every channel.
5. Save the figure to `7_channels_mean_and_psd15hz.pdf`.

---

## Key Parameters

All tunable parameters are located at the top of each script:

| Parameter | Location | Default | Description |
| :--- | :--- | :--- | :--- |
| `SCREEN_REFRESH_RATE` | `ssvep.py` | `60` | Monitor refresh rate (Hz). Must match your hardware. |
| `STIM_FREQUENCY` | `ssvep.py` | `4` | Target flicker frequency (Hz). |
| `TRIAL_NUM` | `ssvep.py` | `6` | Number of stimulation trials. |
| `STIM_DURATION` | `ssvep.py` | `1.0` | Duration of each stimulus (seconds). |
| `REST_DURATION` | `ssvep.py` | `1.0` | Rest duration between trials (seconds). |
| `EEG_IP` / `PORT` | `NeuraDock_socket.py` | `'10.187.255.187'` / `9600` | NeuraDock TCP endpoint. |
| `fs` | `ssvep_result.py` | `250` | EEG sampling rate (Hz). |
| `epoch_len` | `ssvep_result.py` | `1000` | Epoch length in samples (4 s at 250 Hz). |

---

## Data Format

The recorded `1.txt` uses the NeuraDock raw CSV format:

```
HEADER_DEF,_,C,C,C,C,C,C,C
<timestamp>,<seq>,ch0,ch1,ch2,ch3,ch4,ch5,ch6,
...
marker
...
```

- **7 channels**: PO4, O2, T6, Oz, T5, O1, PO3
- **Sampling rate**: 250 Hz
- **Markers**: The string `marker\n` is inserted at the exact onset of each stimulation block.

---

## Notes

- **Timing Precision**: SSVEP stimulation relies on frame-perfect flipping. Keep other applications closed during `ssvep.py` to avoid frame drops.
- **Marker Synchronization**: The marker is written **immediately before** the visual flip loop begins, so the EEG epoch should be aligned to stimulus onset with minimal latency.
- **Filter Settings**: `ssvep_result.py` uses a 2–80 Hz Butterworth bandpass. Adjust `lowcut` / `highcut` in the script if your target frequency lies outside this range.
- **Channel Count**: The analysis script auto-detects the number of channels from the data shape. If you use fewer than 7 channels, the plots will adapt automatically.

---

## Troubleshooting

| Issue | Solution |
| :--- | :--- |
| PsychoPy window is black or freezes | Update graphics drivers; ensure `fullscr=False` for debugging. |
| No markers in `1.txt` | Check file permissions; verify `NeuraDock_socket.py` is running before `ssvep.py`. |
| `ssvep_result.py` shows "No valid epochs" | Confirm `epoch_len` does not exceed the interval between two consecutive markers. |
| Peaks appear at wrong frequency | Double-check `SCREEN_REFRESH_RATE` matches your monitor; verify `fs` matches the device sampling rate. |

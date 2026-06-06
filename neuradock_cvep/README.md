# c-VEP BCI Speller — NeuraDock

This directory contains a complete **code-modulated Visual Evoked Potential (c-VEP)** brain-computer interface (BCI) pipeline based on the NeuraDock dry-electrode EEG device.

Unlike SSVEP (which encodes each target with a different *frequency*), c-VEP encodes each target with a different *circular shift* of the **same pseudo-random m-sequence**. The pipeline covers **template calibration**, **real-time multi-target stimulus presentation**, **online decoding (TTCA)**, and a file-based mechanism to synchronize stimulation and classification.

---

## File Overview

| File | Description |
| :--- | :--- |
| `calibration.py` | **Template Calibration**. Presents a single flickering box driven by each class's m-sequence, records the evoked EEG, and saves four averaged templates (`template1.npy` … `template4.npy`). Run this **first**. |
| `online_test.py` | **Online Speller**. Presents 4 simultaneously flickering targets (A/B/C/D), records each trial, decodes it with the TTCA model, and feeds the prediction back to the on-screen UI to spell a 6-letter sequence. Reports accuracy. |
| `ttca.py` | **TTCA Decoder** (`TTCA` class). A filter-bank + temporal response function (TRF) reconstruction + spatial-filter (TDCA-style) correlation classifier. Loads the four templates and scores each test trial against the reconstructed responses of all four classes. |
| `neuradock_socket.py` | **TCP Data Stream Client** (`DataStream` class). Connects to the NeuraDock device over TCP, decodes incoming packets, and continuously appends the EEG samples to `1.txt` in CSV format. |
| `quality.py` | **Signal Quality Control**. Computes per-channel quality metrics (50 Hz line noise, EMG, baseline drift, abnormal-value count, spectral band ratios) and rejects bad trials against pre-computed thresholds (`thresholds.csv`). |
| `black.png` / `white.png` | Stimulus images used for the OFF (0) and ON (1) states of each m-sequence bit. |

---

## How c-VEP Encoding Works

All four targets share **one** m-sequence; the targets differ only in how far that sequence is circularly shifted.

| Property | Value | Where defined |
| :--- | :--- | :--- |
| m-sequence | 6-bit LFSR, seed `[0,0,0,0,0,1]`, feedback `coef[-1] ^ coef[-2]` | `get_mseq()` in both scripts |
| Sequence period | **63** chips (maximal-length) | — |
| Frames per chip | **×3** | `m1 = [i for i in m1 for j in range(3)]` |
| Frames per trial | **189** (63 × 3) | stimulation loop `range(189)` |
| Targets / classes | **4**, via circular shifts of **12 / 24 / 36 frames** (= 4 / 8 / 12 chips) | `mm = [m1, m1[12:]+m1[:12], …]` |
| Display refresh | **60 Hz** → 189 frames = **3.15 s** per trial | hardware |
| EEG sampling | **250 Hz** → **788 samples** per trial | `data1 = np.zeros((…, 7, 788))` |
| Channels | **7** occipital channels | device |

> The same `get_mseq` / `×3` / shift definitions appear in `calibration.py` and `online_test.py`, so the templates recorded during calibration match the codes shown during the online test. If you change any of these (sequence, repeat factor, shifts, or trial length), you **must** change them in both files and re-run calibration.

---

## System Requirements

- **Python**: 3.9 or 3.10 (PsychoPy compatibility)
- **NeuraDock Device**: connected to the same LAN as the PC, streaming 7 channels at 250 Hz
- **Monitor Refresh Rate**: 60 Hz (the 189-frame / 788-sample relationship assumes 60 Hz display + 250 Hz EEG)

### Python Dependencies

```bash
pip install numpy scipy matplotlib pandas scikit-learn mne psychopy
```

---

## Experiment Workflow

### Step 0 — Configure the device endpoint

In **both** `calibration.py` and `online_test.py`, set the NeuraDock IP/port near the top:

```python
pp = DataStream(IP='172.17.144.1', PORT=9600, save_filepath="1.txt")
```

Update the `IP` to match your device. Both scripts start the acquisition thread themselves (`pp.run_DataStream`), so you do **not** need to run `neuradock_socket.py` separately.

### Step 1 — Calibration (record templates)

```bash
python calibration.py
```

- A countdown is shown, then a single center box flickers for **189 frames** per trial.
- For each of the 4 classes, multiple trials are collected (default: until **20** qualified trials per class).
- A `marker\n` line is written to `1.txt` at the onset of every trial, and the recorded data is sliced into trials anchored on those markers.
- Output: `template1.npy`, `template2.npy`, `template3.npy`, `template4.npy` (shape `(n_trials, 7, 788)`), averaged later by the decoder.
- Press **ESC** to abort.

> Quality control (`quality_control`) is **disabled by default** in `calibration.py` (`qualified_trials = data1`). Re-enable it if you want bad trials rejected before they enter the templates — this requires a `thresholds.csv` produced by `quality.cal_thresholds`.

### Step 2 — Online Speller

```bash
python online_test.py
```

- Loads the four templates and builds the `TTCA` decoder in a background thread (`fun2`).
- Presents 4 flickering targets and a prompt asking the user to focus on a sequence of 6 letters.
- For each letter:
  1. A cue period is shown, then the 189-frame stimulation plays.
  2. The script writes `trigger.txt` to tell the decoder a trial is ready.
  3. The decoder reads the 788-sample trial, predicts a class, and writes the result to `target.txt`.
  4. The selected letter turns **green** (correct) or **red** (incorrect).
- At the end, the console prints `acurancy: <right>/<total>`.

---

## Inter-Process Communication (file-based)

Stimulation and decoding run as separate threads and coordinate through small text files in the working directory:

| File | Writer | Reader | Purpose |
| :--- | :--- | :--- | :--- |
| `1.txt` | `DataStream` (acquisition) | calibration / online | Raw CSV EEG stream; cleared after each block. |
| `marker\n` (line in `1.txt`) | stimulus loop | parser | Marks trial onset for epoch slicing. |
| `trigger.txt` | `online_test.stimulate` | `online_test.fun2` | Signals "a trial has finished, decode it now". |
| `target.txt` | `online_test.fun2` | `online_test.stimulate` | Carries the predicted class index back to the UI. |

> Because coordination is done through files, always run the scripts from this directory, and make sure no stale `trigger.txt` / `target.txt` / `1.txt` remain from a previous run.

---

## Key Parameters

| Parameter | Location | Default | Description |
| :--- | :--- | :--- | :--- |
| m-sequence seed | `get_mseq([0,0,0,0,0,1])` | 6-bit | LFSR initial state; sets the 63-chip code. |
| Frames per chip | `for j in range(3)` | `3` | Frames each m-sequence chip is held. |
| Class shifts | `mm = [m1, m1[12:]+…]` | 12/24/36 | Circular shift (frames) between the 4 targets. |
| Frames per trial | stimulation `range(189)` | `189` | 63 chips × 3 frames. |
| Samples per trial | `np.zeros((…,7,788))` | `788` | 189 frames @60 Hz → 3.15 s @250 Hz. |
| Letters to spell | `online_test.py` | `6` | Length of the online test sequence. |
| Trials per class | `qualified_num >= 20` | `20` | Calibration trials collected per template. |
| `winLEN` | `ttca.py` | `4.13` | Decoder analysis window (s). Sliced against the available samples. |
| `srate` | `ttca.py` | `250` | EEG sampling rate (Hz). |
| `n_band` | `ttca.py` | `5` | Number of filter-bank sub-bands. |
| `IP` / `PORT` | both scripts | `172.17.144.1` / `9600` | NeuraDock TCP endpoint. |

---

## Data Format

The recorded `1.txt` uses the NeuraDock raw CSV format, one time-point per line:

```
,<seq>,ch0,ch1,ch2,ch3,ch4,ch5,ch6
...
marker
...
```

- **7 channels**, occipital montage (e.g. PO4, O2, T6, Oz, T5, O1, PO3).
- **Sampling rate**: 250 Hz.
- **Markers**: the literal line `marker\n` is inserted at the exact onset of each stimulation trial; parsers reset their sample counter on this line.

Each calibration block parses `1.txt` into an array of shape `(trials, 7, 788)`; each online trial is `(1, 7, 788)`.

---

## Notes

- **Timing precision**: c-VEP decoding depends on frame-accurate flipping and tight marker alignment. Close other applications during stimulation to avoid dropped frames.
- **Codebook must match**: the templates are only valid for the exact m-sequence, repeat factor, shifts, and trial length used at calibration time. Re-calibrate after any change.
- **Inter-class shifts**: the default shifts (4 / 8 / 12 chips out of 63) are relatively small; if classes are frequently confused, spreading the shifts more widely across the 63 chips can improve separability.
- **Single-point parsing**: when a CSV line fails to parse, the current parser substitutes a synthetic segment and stops filling the rest of that trial — a single corrupt sample therefore discards the whole trial. Keep the link stable, or harden the parsing loop if dropouts are common.

---

## Troubleshooting

| Issue | Solution |
| :--- | :--- |
| `FileNotFoundError: template1.npy` | Run `calibration.py` first to generate the four templates. |
| Connection error on startup | Verify the `IP`/`PORT` in `DataStream(...)` match your NeuraDock device and that it is on the same LAN. |
| Decoder never fires / hangs | Check for a leftover `trigger.txt` or `target.txt`; delete stale files and restart. |
| PsychoPy window is black or freezes | Update graphics drivers; keep `fullscr=False` while debugging. |
| Low online accuracy | Re-run calibration with more trials, confirm 60 Hz refresh, and verify the same m-sequence/shifts are used in both scripts. |

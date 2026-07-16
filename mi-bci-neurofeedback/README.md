# Motor-Imagery Neurofeedback (Live EEG)

A live **motor-imagery neurofeedback** example for the NeuraDock EEG Workstation. This directory is an unmodified, packaged copy of the field-tested experiment workflow supplied with this example:

1. collect a calibration session with threshold-based feedback;
2. extract spectral, Hjorth, and coherence features and train an RBF-SVM; and
3. run a second session using the trained model for online feedback.

The visual paradigm uses the supplied hand images and black/white circular targets. EEG samples are received over TCP and stored in a temporary `1.txt` file; each trial is synchronized by a `marker` line.

> **Important — research prototype.** This example is intended for supervised research and engineering use with a known-good NeuraDock setup. It is not medical software and must not be used for diagnosis, treatment decisions, or unattended operation.

## Files

| File | Purpose |
|---|---|
| `full_test.py` | The original three-stage calibration, SVM-training, and online-test workflow. |
| `neuradock_socket.py` | The original TCP receiver that writes the 7 used EEG channels to `1.txt`. |
| `hand_open.png`, `hand_close.png` | Local visual-feedback assets used by `full_test.py`. |
| `white.png`, `black.png` | Local target assets used by the stimulation sequence. |

The six runtime files above are intentionally retained without source changes. Do not rename the image files: `full_test.py` loads them by their current names.

## Requirements

- Python 3.9–3.10 recommended (PsychoPy compatibility)
- A NeuraDock EEG Workstation reachable through TCP
- A display suitable for full-screen PsychoPy presentation

Install the Python packages:

```bash
python -m pip install -r requirements.txt
```

## Device configuration

Before running, inspect these values at the end of `neuradock_socket.py`:

```python
pp = DataStream("192.168.214.102", 9600, save_filepath="1.txt")
```

Set the IP address and port for the connected device if necessary. The current field-tested configuration receives 8 hardware values per time point and writes the first 7 values. The analysis in `full_test.py` assumes this channel order:

```text
T5, T6, PO3, PO4, O1, Oz, O2
```

Do not change the order in only one script; the receiver, recorded data, and `CH_MAP` must stay aligned.

## Run the experiment

Use two terminals in this folder.

**Terminal 1 — start EEG recording**

```bash
python neuradock_socket.py
```

Keep this process running. It connects to the device and appends live samples to `1.txt`.

**Terminal 2 — start the full workflow**

```bash
python full_test.py
```

`full_test.py` clears `1.txt` at the beginning, then performs the following automatically:

1. **Calibration:** runs the visual paradigm and saves `data_online_test_train.npy`.
2. **Model training:** filters trials, extracts features, and searches an RBF-SVM pipeline.
3. **Online test:** runs a second visual paradigm using the newly trained model and saves `data_online_test_test.npy`.

Press `Esc` during the paradigm to end the current run. Do not stop the receiver until the experiment has finished writing its session data.

## Data and generated files

The generated `1.txt`, `data_*.npy`, reports, and plots are ignored by Git. They can contain raw EEG or participant-derived results and should be stored, governed, and shared according to your study protocol.

The repository does not include any participant recordings. When publishing results, use de-identified data only and obtain the required ethics and consent approvals.

## Troubleshooting

- **`DATA ERROR: Please check connection`** — verify that `neuradock_socket.py` is running, the IP/port is correct, and `1.txt` is being updated.
- **PsychoPy cannot open a window** — use a supported desktop environment and a Python/PsychoPy version compatible with your GPU drivers.
- **Too few valid trials to train** — inspect electrode contact, motion artefacts, and the quality thresholds in the field-tested script before repeating the calibration session.
- **Different channel montage** — this workflow is tied to the listed 7-channel order. A montage change requires validated changes to the acquisition and analysis configuration; it is not a drop-in setting change.

## Provenance

This GitHub example packages the original `full_test.py` workflow and its required local image assets without altering their operational code. Documentation and Git-ignore rules are the only added project files.

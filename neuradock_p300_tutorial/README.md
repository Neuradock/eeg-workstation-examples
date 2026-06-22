# NeuraDock P300 Experiment Tutorial

This repository contains a minimal visual P300 oddball experiment for NeuraDock EEG streaming. It is designed for teaching and reproducible lab demos: one script displays target/background stimuli, sends event markers, receives EEG packets over TCP, and saves round-level data files.

## What is included

```text
.
├── assets/
│   ├── target.png          # Put or replace the target stimulus image here
│   └── background.jpg      # Put or replace the background/non-target image here
├── output/
│   └── .gitkeep            # Experiment outputs are ignored by Git
├── src/
│   ├── neuradock_stream.py # NeuraDock TCP stream reader
│   └── p300_experiment.py  # P300 experiment runner
├── .gitignore
├── README.md
└── requirements.txt
```

## Hardware mode

This tutorial uses the NeuraDock TCP stream interface. USB and Bluetooth modes can both appear as a TCP service, depending on the NeuraDock bridge software.

Default stream settings:

```python
IP = "127.0.0.1"
PORT = 9600
total_channels = 8
used_channels = 7
pkg_groups = 1
data_group_len = 250
```

If your NeuraDock service is on another computer, pass its IP address with `--ip`.

## Installation

Create a Python environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

## Prepare images

Place your stimulus images in `assets/`:

- Target stimulus: `assets/target.png`
- Background or non-target stimulus: `assets/background.jpg`

You can also use any other paths at runtime:

```bash
python src/p300_experiment.py --target-image path/to/target.png --background-image path/to/background.jpg
```

## Run the experiment

Start the NeuraDock TCP stream service first, then run:

```bash
python src/p300_experiment.py --subject S01
```

Common options:

```bash
python src/p300_experiment.py ^
  --ip 127.0.0.1 ^
  --port 9600 ^
  --subject S01 ^
  --rounds 2 ^
  --trials 50 ^
  --target-image assets/target.png ^
  --background-image assets/background.jpg
```

Use `--windowed` for debugging without fullscreen:

```bash
python src/p300_experiment.py --subject test --windowed
```

Press `ESC` during the experiment to stop early.

## Output files

Each run creates a timestamped folder under `output/`, for example:

```text
output/S01_20260622_153000/
├── S01_20260622_153000.txt   # Continuous EEG text log with marker lines
├── config.json               # Runtime configuration
├── eeg_1.npy                 # Round 1 EEG array, shape: channels x samples
├── eeg_stamp_1.csv           # Packet timestamps and packet lengths
└── marker_1.csv              # Trial-level marker table
```

Marker codes:

- `1`: target stimulus
- `2`: background/non-target stimulus

The `output/` folder is ignored by Git to avoid accidentally uploading participant data.

## Notes for scientific use

- Verify monitor timing and event alignment before collecting formal data.
- Keep participant identifiers out of filenames if the repository is public.
- Back up raw data outside this repository.
- This tutorial is an acquisition example only; offline ERP/P300 analysis is intentionally not included.

## Troubleshooting

If the script cannot connect, check that the NeuraDock stream service is running and that `--ip` / `--port` are correct.

If packets are skipped, confirm that the stream format matches `total_channels * pkg_groups` numeric values after the first two packet fields.

If no window appears, try:

```bash
python src/p300_experiment.py --windowed
```

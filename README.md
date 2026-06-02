# NeuraDock EEG Workstation Examples

This repository contains example EEG workflows and demos for **NeuraDock EEG Workstation**.

NeuraDock EEG Workstation is a 7-channel dry-electrode EEG development kit for researchers, developers, and makers working with brain signals.

This repository focuses on complete example workflows, including signal quality checks, visual evoked potential experiments, real-time marker workflows, and advanced research demos.

## Repository Scope

This repository is used for:

- Complete EEG example workflows
- Experiment demos
- Signal processing examples
- SSVEP and cVEP workflows
- Signal quality evaluation examples
- Real-time marker workflows
- Advanced research examples

This repository is **not** used for:

- NeuraDock Recording Software releases
- Basic Python data readers only
- Large public sample datasets
- Full agent workflow logic
- Full hardware design files

Related repositories:

| Repository | Purpose |
|---|---|
| [eeg-workstation](https://github.com/Neuradock/eeg-workstation) | Main project overview and repository navigation |
| [eeg-workstation-docs](https://github.com/Neuradock/eeg-workstation-docs) | Documentation, setup guides, data format notes, tutorials, and hardware interface notes |
| [eeg-workstation-software](https://github.com/Neuradock/eeg-workstation-software) | NeuraDock Recording Software releases and software usage notes |
| [eeg-workstation-python](https://github.com/Neuradock/eeg-workstation-python) | Python tools, notebooks, and EEG data reading examples |
| [eeg-workstation-agent](https://github.com/Neuradock/eeg-workstation-agent) | EEG Agent workflows, prompts, and analysis pipelines |
| [eeg-workstation-examples](https://github.com/Neuradock/eeg-workstation-examples) | Example EEG demos and signal processing workflows |
| [eeg-workstation-sample-data](https://github.com/Neuradock/eeg-workstation-sample-data) | Public sample EEG datasets for tutorials and examples |
| [eeg-workstation-hardware](https://github.com/Neuradock/eeg-workstation-hardware) | Hardware interface and port specifications for third-party integration |

## Channel Layout

The default 7-channel electrode layout is:

```text
O1, O2, Oz, PO3, PO4, CP5, CP6
```

Example workflows in this repository should preserve this channel order unless otherwise stated.

## Example Workflows

This repository is being organized from existing NeuraDock tutorial materials, example code, and research demos.

| Example | Directory | Description | Status |
|---|---|---|---|
| Signal Quality Check | `signal-quality/` | Inspect basic EEG signal quality using recorded NeuraDock data | Preparing |
| SSVEP Workflow | `ssvep/` | Visual stimulation and offline SSVEP analysis workflow | available |
| Real-Time Marker Workflow | `marker/` | Inject event markers into real-time EEG data streams | available |
| cVEP Workflow | `cvep/` | Code-modulated visual evoked potential workflow | Planned |
| Eyes-Open / Eyes-Closed | `eyes-open-closed/` | Basic EEG comparison workflow for signal inspection and alpha activity observation | available |
| Band Power Analysis | `band-power/` | Frequency band power calculation and visualization | available |
| PSD Visualization | `psd/` | Power spectral density visualization for EEG signals | Planned |
| Visual Reconstruction Demo | `visual-reconstruction/` | Advanced EEG visual reconstruction research example | available |

## Recommended Repository Structure

The recommended structure is:

```text
eeg-workstation-examples/
├── README.md
├── signal-quality/
│   ├── README.md
│   └── signal_quality_check.ipynb
├── ssvep/
│   ├── README.md
│   ├── ssvep.py
│   ├── ssvep_result.py
│   ├── NeuraDock_socket.py
│   ├── Neuradock_lib.py
│   ├── black.png
│   └── white.png
├── real-time-marker/
│   ├── README.md
│   └── neuradock_marker.py
├── cvep/
│   ├── README.md
│   ├── calibration.py
│   ├── online_test.py
│   ├── quality.py
│   ├── ttca.py
│   ├── black.png
│   └── white.png
├── eyes-open-closed/
│   └── README.md
├── band-power/
│   └── README.md
├── psd/
│   └── README.md
└── visual-reconstruction/
    └── README.md
```

The exact file structure will be finalized as the cleaned examples are added.

## Signal Quality Check

The signal quality workflow helps users inspect basic EEG data quality using recorded NeuraDock data.

This example is based on the existing NeuraDock tutorial:

```text
NeuraDock系统和信号质量评估
```

Related documentation:

- [Signal Quality Check](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/signal-quality.md)

Expected directory:

```text
signal-quality/
```

Expected materials:

```text
signal-quality/README.md
signal-quality/signal_quality_check.ipynb
```

Sample data should be maintained in:

- [eeg-workstation-sample-data](https://github.com/Neuradock/eeg-workstation-sample-data)

## SSVEP Workflow

The SSVEP workflow demonstrates a basic steady-state visual evoked potential experiment.

This example is based on the existing NeuraDock tutorial:

```text
基于Python的SSVEP教程 (Online刺激 + Offline分析)
```

The workflow includes:

- Visual flicker stimulation
- Marker output
- EEG recording
- Offline preprocessing
- Epoching
- ERP or trial averaging
- Welch PSD analysis
- Stimulation frequency and harmonic inspection

Related documentation:

- [SSVEP Workflow](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/ssvep.md)

Expected directory:

```text
ssvep/
```

Expected materials from the existing tutorial code include:

```text
ssvep.py
ssvep_result.py
NeuraDock_socket.py
Neuradock_lib.py
black.png
white.png
```

The cleaned official example should include a local `README.md` explaining how to run the online stimulation and offline analysis scripts.

## Real-Time Marker Workflow

The real-time marker workflow demonstrates how to attach event markers to incoming EEG data in a real-time experiment workflow.

This example is based on the existing NeuraDock tutorial:

```text
NeuraDock实时数据流打标
```

The workflow uses a producer-consumer architecture based on Python `threading` and `queue.Queue`.

Related documentation:

- [Real-Time Marker Workflow](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-marker.md)

Expected directory:

```text
real-time-marker/
```

Expected materials:

```text
real-time-marker/README.md
real-time-marker/neuradock_marker.py
```

## cVEP Workflow

The cVEP workflow is planned as a code-modulated visual evoked potential example.

The existing code materials appear to include a `neuradock_cvep/` folder.

Expected directory:

```text
cvep/
```

Expected materials may include:

```text
calibration.py
online_test.py
quality.py
ttca.py
black.png
white.png
```

The exact file list and workflow should be confirmed by the technical team before public release.

## Eyes-Open / Eyes-Closed Workflow

The eyes-open / eyes-closed workflow is planned as a basic EEG comparison example.

It may be used for:

- Basic EEG signal inspection
- Resting-state data inspection
- Alpha activity observation
- Demoing simple offline analysis

Expected directory:

```text
eyes-open-closed/
```

The exact analysis script, notebook, and sample data should be confirmed by the technical team.

## Band Power Analysis

The band power workflow is planned as a basic frequency-domain EEG analysis example.

It may be used for:

- Calculating EEG frequency band power
- Comparing band power across channels
- Visualizing simple EEG features
- Preparing features for downstream analysis

Expected directory:

```text
band-power/
```

The exact script, notebook, frequency bands, and plotting output should be confirmed by the technical team.

## PSD Visualization

The PSD workflow is planned as a basic power spectral density visualization example.

It may be used for:

- Inspecting EEG frequency-domain structure
- Comparing channels
- Checking signal quality
- Supporting example analysis workflows such as SSVEP

Expected directory:

```text
psd/
```

If this directory is mentioned in documentation or README files, it should either be created or removed from the public documentation until ready.

## Visual Reconstruction Demo

The visual reconstruction demo is an advanced research example based on NeuraDock EEG data.

Existing external repository:

- [EEG_Visual_Reconstruction_NeuraDock](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock)

This demo should be treated as an advanced example, not as a basic getting-started workflow.

Before migrating or linking it as an official example, the team should confirm:

- License
- Data availability
- Dependency requirements
- Model weights or external resources
- Reproducibility
- Whether the repository should be transferred, forked, or referenced externally

Expected directory if integrated later:

```text
visual-reconstruction/
```

## Working with Sample Data

Reusable public sample datasets should be maintained in:

- [eeg-workstation-sample-data](https://github.com/Neuradock/eeg-workstation-sample-data)

Example workflows should avoid committing large datasets directly into this repository.

Each example should clearly state:

- Required data file
- Expected data format
- Channel layout
- Whether live hardware is required
- Whether sample data can be used instead
- How to modify local file paths

## Dependency Notes

Some examples may depend on packages used by:

- [eeg-workstation-python](https://github.com/Neuradock/eeg-workstation-python)

Examples involving stimulus presentation may require additional dependencies, such as PsychoPy or other visual presentation tools.

Each example directory should include its own `README.md` that states:

- Required Python version
- Required packages
- Required hardware
- Required sample data
- How to run the example
- Expected output
- Known limitations

## Related Documentation

| Document | Description |
|---|---|
| [Getting Started](https://github.com/Neuradock/eeg-workstation-docs/blob/main/getting-started.md) | First-time setup guide for NeuraDock EEG Workstation |
| [Software Installation](https://github.com/Neuradock/eeg-workstation-docs/blob/main/software-installation.md) | Software environment setup and installation guide |
| [Data Format](https://github.com/Neuradock/eeg-workstation-docs/blob/main/data-format.md) | EEG text file structure, channel layout, USB data format, and Bluetooth data format |
| [USB Real-Time Data Streaming](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-streaming-usb.md) | Read real-time EEG data through the USB workflow |
| [Bluetooth Real-Time Data Streaming](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-streaming-bluetooth.md) | Read real-time EEG data through the Bluetooth workflow |
| [Read USB Text Files](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/read-txt-usb.md) | Read and parse EEG text files recorded from the USB workflow |
| [Read Bluetooth Text Files](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/read-txt-bluetooth.md) | Read and parse EEG text files recorded from the Bluetooth workflow |
| [Real-Time Marker Workflow](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/real-time-marker.md) | Stream EEG data with event markers for experiment synchronization |
| [Signal Quality Check](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/signal-quality.md) | Evaluate basic EEG signal quality from recorded NeuraDock data |
| [SSVEP Workflow](https://github.com/Neuradock/eeg-workstation-docs/blob/main/tutorials/ssvep.md) | Run visual stimulation and offline SSVEP analysis workflows |
| [Troubleshooting](https://github.com/Neuradock/eeg-workstation-docs/blob/main/troubleshooting.md) | Common connection, data recording, and software issues |

## Links

- Website: [neuradock.com](https://neuradock.com)
- Crowd Supply: [NeuraDock EEG Workstation](https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation)
- YouTube: [@NeuraDock](https://www.youtube.com/@NeuraDock)
- Discord: NeuraDock Community

## License

The license for this repository will be provided before public release.

Unless otherwise stated, software code, documentation, sample data, and hardware interface materials may use different licenses across the NeuraDock GitHub organization.

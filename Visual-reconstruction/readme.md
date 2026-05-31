<h1 id="english">NeuraDock EEG Visual Reconstruction</h1>

> **Project Repository**: [https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock)

---

## Overview

This project demonstrates **visual image reconstruction from EEG signals** using the NeuraDock dry-electrode device. It reproduces and adapts the guided-diffusion-based reconstruction pipeline from the NeurIPS 2024 paper, achieving high-fidelity image restoration from only **7-channel occipital EEG recordings**.

If you are looking for a complete end-to-end system that covers stimulus presentation → signal acquisition → preprocessing → deep-learning reconstruction, please visit the repository above.

---

## Highlights

| Feature | Description |
|---------|-------------|
| **Hardware** | NeuraDock 7-channel dry electrode (250 Hz) |
| **Paradigm** | RSVP (Rapid Serial Visual Presentation) with automatic event marking |
| **Preprocessing** | Band-pass (1–100 Hz) + notch (50 Hz) + mvnn artifact removal |
| **Model** | Guided-diffusion visual decoder (adapted from Li et al., 2024) |
| **Performance** | Comparable to 128-channel research-grade systems after 1.5× data augmentation |

---

## Quick Links

- **Source Code**: [GitHub — xzy286/EEG_Visual_Reconstruction_NeuraDock](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock)
- **Paper**: *Visual decoding and reconstruction via EEG embeddings with guided diffusion* (arXiv:2403.07721)
- **Hardware**: [NeuraDock Official Site](https://www.neuradock.com/)

---

## What You Will Find in the Repository

```text
├── acquisition/          # RSVP stimulation + real-time EEG acquisition
├── preprocessing/        # MNE-based preprocessing pipeline
├── Generation/           # Core guided-diffusion reconstruction model
├── Generation_adapters/  # NeuraDock-specific adapter scripts
├── data/                 # Dataset storage
└── notebooks/            # Visualization & analysis demos
```

---

## Workflow in 3 Steps

1. **Acquisition** — Run `neuradock_rsvp.exe` to present visual stimuli and record EEG with event markers.
2. **Preprocessing** — Execute `neuradock_preprocessing.py` to filter, clean, and epoch the raw data.
3. **Reconstruction** — Replace adapter files in `Generation/` and run `ATMS_reconstruction_neuradock.py` to generate images from EEG embeddings.

For detailed installation instructions, environment setup, and quantitative results, please refer to the **[README in the repository](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock/blob/main/README.md)**.

---

## License

The project is licensed under the [MIT License](https://github.com/xzy286/EEG_Visual_Reconstruction_NeuraDock/blob/main/LICENSE).

---

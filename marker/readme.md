# NeuraDock Real-Time EEG Stream with Event Markers

Lightweight Python module for real-time TCP streaming from the **NeuraDock** dry-electrode EEG device, with built-in trigger / event marker injection.

---

## Overview

`neuradock_marker.py` provides two core classes:

| Class | Purpose |
|-------|---------|
| `DataStream` | Low-level TCP client that connects to NeuraDock, receives raw text packets, parses them into `(samples, channels)` arrays, and yields them chunk by chunk. |
| `EEGThreadManager` | High-level wrapper that runs `DataStream` in a background thread, buffers samples into a thread-safe queue, and automatically appends an extra **marker column** to every sample for event synchronization (e.g., SSVEP, cVEP, ERP paradigms). |

---

## Files

| File | Description |
|------|-------------|
| `neuradock_marker.py` | Main module (pure Python, no external dependencies except `numpy`). |

---

## Dependencies

- Python ≥ 3.8
- `numpy`

```bash
pip install numpy
```

---

## Quick Start

```python
from neuradock_marker import EEGThreadManager
import time

# 1. Create manager and start background acquisition
mgr = EEGThreadManager()
ok = mgr.start_stream()
if not ok:
    raise RuntimeError("Failed to start EEG stream.")

# 2. Collect baseline (no trigger)
time.sleep(2.0)

# 3. Inject event marker, run stimulus, then clear marker
mgr.set_trigger(1)      # Event code = 1
time.sleep(5.0)         # Stimulus ON period
mgr.set_trigger(0)      # Back to baseline

# 4. Collect a bit more post-stimulus data
time.sleep(2.0)

# 5. Stop stream and flush all queued data into a list
mgr.stop_stream()
buf = []
mgr.flush_to_buffer(buf)

# buf is now a list of np.ndarray, each with shape (n_samples, 8)
# where the last column is the injected trigger/marker.
import numpy as np
data = np.vstack(buf)
print("Collected shape:", data.shape)   # (N, 8)  — 7 EEG channels + 1 marker
```

---

## API Reference

### `DataStream(IP, PORT, **kwargs)`

Iterator-style TCP client.

**Parameters**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `IP` | — | NeuraDock host IP address. |
| `PORT` | — | TCP port number. |
| `buffer_size` | `1024` | Socket receive buffer size (bytes). |
| `total_channels` | `8` | Hardware channels per packet (including auxiliary). |
| `used_channels` | `7` | Valid EEG channels to retain. |
| `pkg_groups` | `1` | Sample packets per line (`1` for USB, `5` for Bluetooth). |
| `data_group_len` | `1` | Number of samples yielded per `next()` call. |

**Usage**

```python
stream = DataStream("192.168.56.1", 9600, pkg_groups=5)
for sample_group in stream:
    # sample_group is a list of lists: shape (data_group_len, used_channels)
    process(sample_group)
```

---

### `EEGThreadManager()`

Thread-safe manager for background acquisition + marker injection.

**Methods**

| Method | Description |
|--------|-------------|
| `start_stream()` | Open TCP connection and spawn background worker thread. Returns `True` on success. |
| `stop_stream()` | Signal stop, close socket, and join worker thread. |
| `set_trigger(code)` | Set current event marker value (int). Injected into every new sample. |
| `flush_to_buffer(buf)` | Drain the internal queue into an external `list`. |

---

## Data Format

Each queued sample array has shape `(n_samples_per_group, used_channels + 1)`:

| Columns | Content |
|---------|---------|
| `0 … used_channels-1` | EEG channel values (μV) |
| `used_channels` | Event marker / trigger code |

Default configuration (`used_channels=7`) produces arrays with shape `(N, 8)`.

---

## Notes

- The background worker is a **daemon thread**, so it will not block program exit.
- The internal queue has a max size of `100000` samples; if the consumer is slower than the producer, old samples may be silently dropped by the queue (not implemented here — extend if needed).
- Adjust `EEG_IP` and `EEG_PORT` at the top of `neuradock_marker.py` to match your NeuraDock network settings.

"""
NeuraDock EEG Real-Time Data Stream with Event Marker Injection.

This module provides TCP-based streaming classes for NeuraDock dry-electrode EEG devices.
It supports real-time data acquisition, buffering, and automatic trigger/marker injection
into the data stream, which is essential for paradigms such as SSVEP, cVEP, and ERP.
"""

import socket
import threading
import queue

import numpy as np


# Default TCP connection parameters for NeuraDock
EEG_IP = "192.168.56.1"
EEG_PORT = 9600


class DataStream:
    """
    TCP client that streams EEG packets from a NeuraDock device.

    Parameters
    ----------
    IP : str
        IP address of the NeuraDock host.
    PORT : int
        TCP port number.
    buffer_size : int, optional
        Socket receive buffer size in bytes (default: 1024).
    total_channels : int, optional
        Total hardware channels per packet (default: 8).
    used_channels : int, optional
        Number of valid EEG channels to keep (default: 7).
    pkg_groups : int, optional
        Number of sample packets per transmission line (default: 1 for USB, 5 for Bluetooth).
    data_group_len : int, optional
        Number of samples to yield per iteration (default: 1).
    """

    def __init__(
        self,
        IP,
        PORT,
        buffer_size=1024,
        total_channels=8,
        used_channels=7,
        pkg_groups=1,
        data_group_len=1,
    ):
        self.ip = IP
        self.port = PORT
        self.buffer_size = buffer_size
        self.total_channels = total_channels
        self.used_channels = used_channels
        self.pkg_groups = pkg_groups
        self.data_group_len = data_group_len

        self.is_running = False
        self.socket = None
        self._buffer_str = ""
        self._data_buffer = []

    def __iter__(self):
        """Enter streaming mode: connect, reset buffers, and return iterator."""
        if self.is_running:
            self.close()
        self.is_running = True
        self._connect()
        self._buffer_str = ""
        self._data_buffer = []
        return self

    def _connect(self):
        """Establish TCP connection and send the start command."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip, self.port))
            self.socket.send(b"start")
            print(f"[DataStream] Connected to {self.ip}:{self.port}")
        except Exception as e:
            print(f"[DataStream] Connection error: {e}")
            self.is_running = False
            raise

    def close(self):
        """Close the TCP socket and stop the stream."""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    def __next__(self):
        """Fetch the next data group from the stream."""
        if not self.is_running:
            raise StopIteration

        while len(self._data_buffer) < self.data_group_len:
            try:
                chunk = self.socket.recv(self.buffer_size)
                if not chunk:
                    raise ConnectionError("Remote socket closed.")

                self._buffer_str += chunk.decode("utf-8", errors="ignore")

                while True:
                    lines = self._buffer_str.split("\n")
                    if len(lines) < 2:
                        break

                    complete_lines, self._buffer_str = lines[:-1], lines[-1]
                    for line in complete_lines:
                        if not line.strip():
                            continue

                        fields = line.strip().split(",")
                        expected_len = 2 + self.pkg_groups * self.total_channels
                        if len(fields) < expected_len:
                            continue

                        try:
                            data_vals = list(
                                map(
                                    float,
                                    fields[2 : 2 + self.pkg_groups * self.total_channels],
                                )
                            )
                            arr = np.array(data_vals, dtype=np.float32).reshape(
                                self.pkg_groups, self.total_channels
                            )
                            for t in range(self.pkg_groups):
                                self._data_buffer.append(
                                    arr[t, : self.used_channels].tolist()
                                )
                        except ValueError:
                            continue

            except socket.timeout:
                continue
            except Exception:
                self.close()
                raise StopIteration

        res = self._data_buffer[: self.data_group_len]
        self._data_buffer = self._data_buffer[self.data_group_len :]
        return res


class EEGThreadManager:
    """
    Thread-safe manager that runs DataStream in a background thread,
    buffers incoming EEG samples, and injects event markers (triggers).

    Typical workflow::

        mgr = EEGThreadManager()
        mgr.start_stream()          # Start background acquisition
        mgr.set_trigger(1)          # Set current event code
        ...                         # Run experiment / stimulus
        mgr.set_trigger(0)          # Reset trigger to baseline
        mgr.stop_stream()           # Stop and clean up
    """

    def __init__(self):
        self.data_queue = queue.Queue(maxsize=100000)
        self.stop_event = threading.Event()
        self.stream = None
        self.thread = None
        self.current_trigger = 0

    def start_stream(self):
        """
        Start the EEG data stream in a background daemon thread.

        Returns
        -------
        bool
            True if the stream started successfully, False otherwise.
        """
        try:
            self.stream = DataStream(EEG_IP, EEG_PORT)
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            print(f"[Thread Error] Failed to start stream: {e}")
            return False

    def _worker(self):
        """Background worker: consume DataStream, append marker column, and enqueue."""
        print(">> Worker running.")
        try:
            for data_group in self.stream:
                if self.stop_event.is_set():
                    break
                if data_group is None:
                    continue

                arr = np.array(data_group)
                marker = np.full((arr.shape[0], 1), self.current_trigger)
                self.data_queue.put(np.hstack([arr, marker]))
        except Exception as e:
            print(f"[Worker] Exception: {e}")
        finally:
            print(">> Worker stopped.")

    def stop_stream(self):
        """Signal the worker to stop, close the socket, and wait for thread join."""
        self.stop_event.set()
        if self.stream:
            self.stream.close()
        if self.thread:
            self.thread.join(timeout=1.0)

    def flush_to_buffer(self, buf):
        """
        Drain all queued samples into an external list.

        Parameters
        ----------
        buf : list
            Mutable list to receive the flushed numpy arrays.
        """
        while not self.data_queue.empty():
            try:
                buf.append(self.data_queue.get_nowait())
            except queue.Empty:
                break

    def set_trigger(self, code):
        """
        Update the current event marker code.

        Parameters
        ----------
        code : int
            Trigger value to inject into subsequent EEG samples.
        """
        self.current_trigger = int(code)

from __future__ import annotations

import socket
import time
from pathlib import Path
from queue import Queue
from typing import Optional

import numpy as np
import pandas as pd


class NeuraDockStream:
    """TCP data stream reader for NeuraDock EEG data."""

    def __init__(
        self,
        IP: str = "127.0.0.1",
        PORT: int = 9600,
        total_channels: int = 8,
        used_channels: int = 7,
        pkg_groups: int = 1,
        data_group_len: int = 250,
        package_size: int = 512,
        event_queue: Optional[Queue] = None,
        out_dir: Optional[str | Path] = None,
        tag: Optional[str] = None,
        timeout: float = 0.5,
    ) -> None:
        self.ip = IP
        self.port = PORT
        self.total_channels = total_channels
        self.used_channels = used_channels
        self.pkg_groups = pkg_groups
        self.data_group_len = data_group_len
        self.package_size = package_size
        self.event_queue = event_queue
        self.out_dir = Path(out_dir) if out_dir else None
        self.tag = tag
        self.timeout = timeout

        if self.used_channels > self.total_channels:
            raise ValueError("used_channels cannot be larger than total_channels.")

        self.recv_time: list[tuple[float, int]] = []
        self.recv_data: list[np.ndarray] = []
        self.stop_recv = False
        self.is_started = False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.ip, self.port))

    def start_stream(self) -> None:
        self.is_started = True
        self.send_command("start")

    def send_command(self, command: str | bytes) -> int:
        payload = command if isinstance(command, bytes) else command.encode("utf-8")
        return self.socket.send(payload)

    def close(self) -> None:
        self.stop_recv = True
        self.socket.close()

    def run(self, max_recv_time: float = -1) -> None:
        if not self.is_started:
            self.start_stream()

        start_time = time.time()
        realtime_file = None

        if self.tag:
            if self.out_dir:
                self.out_dir.mkdir(parents=True, exist_ok=True)
                realtime_path = self.out_dir / f"{self.tag}.txt"
            else:
                realtime_path = Path(f"{self.tag}.txt")
            realtime_file = open(realtime_path, "a", encoding="utf-8")
            print(f"Continuous EEG text log: {realtime_path}")

        try:
            while not self.stop_recv:
                self._handle_pending_events(realtime_file)

                try:
                    raw = self.socket.recv(self.package_size)
                except socket.timeout:
                    continue

                if not raw:
                    print("NeuraDock stream closed by server.")
                    break

                packet_time = time.time()
                eeg_chunk = self._parse_packet(raw)
                if eeg_chunk is None:
                    continue

                if realtime_file:
                    np.savetxt(realtime_file, eeg_chunk.T, delimiter=",", fmt="%.4f")
                    realtime_file.flush()

                self.recv_data.append(eeg_chunk)
                self.recv_time.append((packet_time, eeg_chunk.shape[1]))

                if max_recv_time > 0 and (packet_time - start_time > max_recv_time):
                    break
        finally:
            if realtime_file:
                realtime_file.close()

    def _handle_pending_events(self, realtime_file) -> None:
        if self.event_queue is None:
            return

        while not self.event_queue.empty():
            command = str(self.event_queue.get())

            if command.startswith("marker:") and realtime_file:
                parts = command.split(":")
                if len(parts) == 5:
                    _, round_num, trial_num, marker_code, timestamp = parts
                    realtime_file.write(
                        f"# MARKER, round={round_num}, trial={trial_num}, "
                        f"code={marker_code}, timestamp={timestamp}\n"
                    )
                    realtime_file.flush()
                else:
                    print(f"Cannot parse marker command: {command}")
                continue

            if command.startswith("round_end:") and self.out_dir:
                round_num = int(command.split(":")[1])
                self._save_round(round_num)
                continue

            if command == "quit":
                self.stop_recv = True

    def _parse_packet(self, raw: bytes) -> Optional[np.ndarray]:
        text = raw.decode("utf-8", errors="ignore").split("\x00", 1)[0].strip()
        parts = text.split(",")
        expected_values = self.total_channels * self.pkg_groups

        if len(parts) < 2 + expected_values:
            print(f"Short packet skipped: expected {2 + expected_values} fields, got {len(parts)}")
            return None

        try:
            values = list(map(float, parts[2 : 2 + expected_values]))
        except ValueError as exc:
            print(f"Packet parse error: {exc}; packet={text[:120]}")
            return None

        eeg_all_channels = np.array(values).reshape(
            (self.total_channels, self.pkg_groups),
            order="F",
        )
        return eeg_all_channels[: self.used_channels, :]

    def _save_round(self, round_num: int) -> None:
        if self.out_dir is None:
            return

        self.out_dir.mkdir(parents=True, exist_ok=True)

        if not self.recv_data:
            print(f"No EEG samples collected for round {round_num}; nothing saved.")
            return

        eeg = np.concatenate(self.recv_data, axis=1)
        np.save(self.out_dir / f"eeg_{round_num}.npy", eeg)
        pd.DataFrame(self.recv_time, columns=["time", "len"]).to_csv(
            self.out_dir / f"eeg_stamp_{round_num}.csv",
            index=False,
        )

        self.recv_data.clear()
        self.recv_time.clear()


DataStream = NeuraDockStream

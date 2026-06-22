from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from queue import Queue
from threading import Thread
from types import SimpleNamespace

import cv2
import numpy as np
import pandas as pd

from neuradock_stream import NeuraDockStream


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a visual P300 oddball experiment with NeuraDock EEG streaming.",
    )
    parser.add_argument("--ip", default="127.0.0.1", help="NeuraDock TCP host.")
    parser.add_argument("--port", type=int, default=9600, help="NeuraDock TCP port.")
    parser.add_argument("--subject", default="test", help="Subject/session label.")
    parser.add_argument("--target-image", default=str(PROJECT_ROOT / "assets" / "target.png"))
    parser.add_argument("--background-image", default=str(PROJECT_ROOT / "assets" / "background.jpg"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"))
    parser.add_argument("--rounds", type=int, default=2, help="Number of experiment rounds.")
    parser.add_argument("--trials", type=int, default=50, help="Trials per round.")
    parser.add_argument("--target-prob-min", type=float, default=0.10)
    parser.add_argument("--target-prob-max", type=float, default=0.25)
    parser.add_argument("--stim-duration", type=float, default=0.20, help="Stimulus duration in seconds.")
    parser.add_argument("--isi", type=float, default=0.80, help="Inter-stimulus interval in seconds.")
    parser.add_argument("--image-width", type=int, default=500, help="Displayed image width in pixels.")
    parser.add_argument("--total-channels", type=int, default=8)
    parser.add_argument("--used-channels", type=int, default=7)
    parser.add_argument("--pkg-groups", type=int, default=1)
    parser.add_argument("--data-group-len", type=int, default=250)
    parser.add_argument("--windowed", action="store_true", help="Use a normal window instead of fullscreen.")
    return parser.parse_args()


def load_centered_image(path: Path, cfg: SimpleNamespace, blank_screen: np.ndarray) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {path}")

    resized = cv2.resize(image, (cfg.image_width, cfg.image_width))
    canvas = blank_screen.copy()
    left = (cfg.screen_w - cfg.image_width) // 2
    top = (cfg.screen_h - cfg.image_width) // 2
    canvas[top : top + cfg.image_width, left : left + cfg.image_width] = resized
    return canvas


def show_stimuli(
    stim_sequence: list[Path],
    markers: list[list[float]],
    cfg: SimpleNamespace,
    blank_screen: np.ndarray,
    event_queue: Queue,
) -> bool:
    target_screen = load_centered_image(cfg.target_image, cfg, blank_screen)
    background_screen = load_centered_image(cfg.background_image, cfg, blank_screen)
    screen_by_path = {
        cfg.target_image: target_screen,
        cfg.background_image: background_screen,
    }

    for trial_idx, image_path in enumerate(stim_sequence, start=1):
        marker_code = 1 if image_path == cfg.target_image else 2
        marker_time = time.time()
        event_queue.put(f"marker:{cfg.round}:{trial_idx}:{marker_code}:{marker_time}")

        cv2.imshow(cfg.window_name, screen_by_path[image_path])
        key_stim = cv2.waitKey(int(cfg.stim_duration * 1000))

        cv2.imshow(cfg.window_name, blank_screen)
        key_isi = cv2.waitKey(int(cfg.isi * 1000))

        elapsed = time.time() - marker_time
        markers.append([cfg.round, marker_code, trial_idx, marker_time, elapsed])

        label = "target" if marker_code == 1 else "background"
        print(f"Round {cfg.round}, trial {trial_idx}/{len(stim_sequence)}: {label}")

        if key_stim == 27 or key_isi == 27:
            print("ESC pressed; stopping experiment.")
            return True

    return False


def make_stimulus_sequence(cfg: SimpleNamespace) -> list[Path]:
    target_prob = random.uniform(cfg.target_prob_min, cfg.target_prob_max)
    n_targets = max(1, int(cfg.trials * target_prob))
    n_background = cfg.trials - n_targets
    sequence = [cfg.target_image] * n_targets + [cfg.background_image] * n_background
    random.shuffle(sequence)
    print(
        f"Round {cfg.round}: target_prob={target_prob:.3f}, "
        f"targets={n_targets}, background={n_background}"
    )
    return sequence


def main() -> None:
    args = parse_args()
    tag = f"{args.subject}_{time.strftime('%Y%m%d_%H%M%S')}"
    out_dir = Path(args.output_dir) / tag
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = SimpleNamespace(
        round=1,
        target_image=Path(args.target_image).resolve(),
        background_image=Path(args.background_image).resolve(),
        trials=args.trials,
        target_prob_min=args.target_prob_min,
        target_prob_max=args.target_prob_max,
        stim_duration=args.stim_duration,
        isi=args.isi,
        image_width=args.image_width,
        screen_w=1920,
        screen_h=1080,
        window_name="NeuraDock P300",
    )

    with open(out_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(vars(args), f, indent=2)

    event_queue: Queue = Queue()
    stream = NeuraDockStream(
        IP=args.ip,
        PORT=args.port,
        total_channels=args.total_channels,
        used_channels=args.used_channels,
        pkg_groups=args.pkg_groups,
        data_group_len=args.data_group_len,
        event_queue=event_queue,
        out_dir=out_dir,
        tag=tag,
    )
    print("Connected to NeuraDock stream.")

    recv_thread = Thread(target=stream.run, daemon=True)
    recv_thread.start()

    cv2.namedWindow(cfg.window_name, cv2.WINDOW_NORMAL)
    if not args.windowed:
        cv2.setWindowProperty(cfg.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        _, _, width, height = cv2.getWindowImageRect(cfg.window_name)
        if width > 0 and height > 0:
            cfg.screen_w, cfg.screen_h = width, height
    except cv2.error:
        pass

    blank_screen = np.zeros((cfg.screen_h, cfg.screen_w, 3), dtype=np.uint8)
    cv2.imshow(cfg.window_name, blank_screen)
    cv2.waitKey(1)

    try:
        for round_num in range(1, args.rounds + 1):
            cfg.round = round_num
            markers: list[list[float]] = []
            sequence = make_stimulus_sequence(cfg)

            print(f"\nRound {round_num}/{args.rounds} starts in 1 second.")
            cv2.waitKey(1000)

            should_quit = show_stimuli(sequence, markers, cfg, blank_screen, event_queue)

            event_queue.put(f"round_end:{round_num}")
            pd.DataFrame(
                markers,
                columns=["round", "marker_code", "trial", "timestamp", "duration_measured"],
            ).to_csv(out_dir / f"marker_{round_num}.csv", index=False)

            if should_quit:
                break

            if round_num < args.rounds:
                cv2.waitKey(1000)
    finally:
        event_queue.put("quit")
        recv_thread.join(timeout=3)
        stream.close()
        cv2.destroyAllWindows()
        print(f"Experiment output saved to: {out_dir}")


if __name__ == "__main__":
    main()

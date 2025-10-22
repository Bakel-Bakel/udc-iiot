#!/usr/bin/env python3
# ==========================================
# Motion Detection & Alert System (OOP)
# Raspberry Pi + Sense HAT + PiCamera2 + Telegram
# ==========================================
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from time import sleep, time
from datetime import datetime
import os
import logging
import requests

from sense_hat import SenseHat
from picamera2 import Picamera2

# ----------------------------
# Configuration
# ----------------------------
@dataclass
class Config:
    # Motion detection
    samples: int = 10           # accel samples to average
    sample_delay: float = 0.01  # seconds between accel samples
    accel_threshold: float = 0.03  # g delta on any axis = motion

    # Camera capture
    image_count: int = 3
    image_interval: float = 1.0   # seconds between images (assignment: 1 s)
    image_size: tuple[int, int] = (1280, 720)
    capture_dir: Path = Path("/home/pi/bakel/captured")

    # LED alarm (assignment: 0.5 s toggle, total 3 s)
    blink_period: float = 0.5
    blink_total: float = 3.0

    # Scheduler
    run_interval: float = 5.0  # seconds

    # Just normal for not spamming social media
    cooldown_seconds: float = 8.0

    # Telegram (read from environment)
    bot_token: str = os.getenv("BOT_TOKEN", "")
    chat_id: str = os.getenv("CHAT_ID", "")


# ----------------------------
# Helpers
# ----------------------------
class TelegramClient:
    def __init__(self, token: str, chat_id: str):
        if not token or not chat_id:
            raise ValueError("BOT_TOKEN and CHAT_ID must be set in environment variables.")
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_photo(self, path: Path) -> dict:
        url = f"{self.base}/sendPhoto"
        with open(path, "rb") as photo:
            r = requests.post(url, data={"chat_id": self.chat_id}, files={"photo": photo}, timeout=30)
        r.raise_for_status()
        return r.json()

    def send_video(self, path: Path) -> dict:
        url = f"{self.base}/sendVideo"
        with open(path, "rb") as vid:
            r = requests.post(url, data={"chat_id": self.chat_id}, files={"video": vid}, timeout=60)
        r.raise_for_status()
        return r.json()


class SenseManager:
    RED = [255, 0, 0]
    WHITE = [255, 255, 255]

    def __init__(self):
        self.sense = SenseHat()
        sleep(0.5)  # tiny settle

        # Baselines
        self.initial_accel = self.sense.get_accelerometer_raw()  # dict with x,y,z (in g)
        ori = self.sense.get_orientation()
        self.initial_pitch = ori["pitch"]
        self.initial_roll = ori["roll"]
        self.initial_yaw = ori["yaw"]

    def get_accel_delta(self, samples: int, delay: float) -> tuple[float, float, float]:
        xs, ys, zs = [], [], []
        for _ in range(samples):
            a = self.sense.get_accelerometer_raw()
            xs.append(a["x"]); ys.append(a["y"]); zs.append(a["z"])
            sleep(delay)
        ax = sum(xs) / len(xs); ay = sum(ys) / len(ys); az = sum(zs) / len(zs)
        dx = abs(self.initial_accel["x"] - ax)
        dy = abs(self.initial_accel["y"] - ay)
        dz = abs(self.initial_accel["z"] - az)
        return dx, dy, dz

    def get_orientation(self) -> tuple[float, float, float]:
        o = self.sense.get_orientation()
        # Return (pitch, roll, yaw)
        return o["pitch"], o["roll"], o["yaw"]

    def blink_alarm(self, period: float, total: float) -> None:
        t0 = time()
        i = 0
        while time() - t0 < total:
            self.sense.clear(self.RED if i % 2 == 0 else self.WHITE)
            sleep(period)
            i += 1
        self.sense.clear()

    def clear(self) -> None:
        self.sense.clear()


class CameraManager:
    def __init__(self, size=(1280, 720)):
        self.cam = Picamera2()
        self.size = size

    def _ensure_preview(self):
        cfg = self.cam.create_preview_configuration(main={"size": self.size})
        self.cam.configure(cfg)

    def capture_burst(self, count: int, interval: float, outdir: Path) -> list[Path]:
        outdir.mkdir(parents=True, exist_ok=True)
        self._ensure_preview()
        self.cam.start()
        files: list[Path] = []
        try:
            for _ in range(count):
                name = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                path = outdir / name
                self.cam.capture_file(str(path))
                files.append(path)
                sleep(interval)
        finally:
            self.cam.stop()
        return files

    def record_video_mp4(self, outpath: Path, seconds: float = 3.0, fps: float = 25.0) -> Path:
        """
        Recorded as h264 and remuxed to mp4 using ffmpeg found on system.
        """
        h264 = outpath.with_suffix(".h264")
        self.cam.video_configuration.size = self.cam.sensor_resolution  # use default full field
        self.cam.video_configuration.controls.FrameRate = fps
        self.cam.start_and_record_video(str(h264), duration=seconds)
        # Remux
        os.system(f"ffmpeg -y -r {int(fps)} -i {h264} -vcodec copy {outpath} >/dev/null 2>&1")
        try:
            h264.unlink(missing_ok=True)
        except Exception:
            pass
        return outpath


# ----------------------------
# Motion system
# ----------------------------
class MotionAlertSystem:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.sense = SenseManager()
        self.cam = CameraManager(size=cfg.image_size)
        self.tg = TelegramClient(cfg.bot_token, cfg.chat_id)
        self._last_alert = 0.0

    def _cooldown_ok(self) -> bool:
        return (time() - self._last_alert) >= self.cfg.cooldown_seconds

    def run_once(self):
        try:
            dx, dy, dz = self.sense.get_accel_delta(self.cfg.samples, self.cfg.sample_delay)
            pitch, roll, yaw = self.sense.get_orientation()

            if dx > self.cfg.accel_threshold or dy > self.cfg.accel_threshold or dz > self.cfg.accel_threshold:
                if not self._cooldown_ok():
                    logging.info("Motion detected but in cooldown; skipping alert.")
                    return

                print("DEVICE MOVED")
                # Assignment order: roll, pitch, yaw
                print(f"Roll = {roll:.1f}°  Pitch = {pitch:.1f}°  Yaw = {yaw:.1f}°")

                # Capture images (3 shots, 1 s apart)
                images = self.cam.capture_burst(
                    self.cfg.image_count, self.cfg.image_interval, self.cfg.capture_dir
                )

                # Send each photo
                for p in images:
                    try:
                        res = self.tg.send_photo(p)
                        logging.info(f"Sent photo: {p.name} -> {res.get('ok')}")
                    except Exception as e:
                        logging.exception(f"Failed to send photo {p}: {e}")

                # Blink LED alarm (0.5 s toggle, 3 s total)
                self.sense.blink_alarm(self.cfg.blink_period, self.cfg.blink_total)

                self._last_alert = time()
            else:
                print("DEVICE IS STILL")
                self.sense.clear()

        except Exception as e:
            logging.exception(f"run_once error: {e}")

    def run_forever(self):
        print("Starting periodic execution... Press Ctrl+C to stop.")
        try:
            while True:
                self.run_once()
                sleep(self.cfg.run_interval)
        except KeyboardInterrupt:
            print("Shutting down. Bye!")
            self.sense.clear()


# ----------------------------
# Entrypoint
# ----------------------------
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    cfg = Config()  # reads BOT_TOKEN and CHAT_ID from env
    system = MotionAlertSystem(cfg)
    system.run_forever()


if __name__ == "__main__":
    main()

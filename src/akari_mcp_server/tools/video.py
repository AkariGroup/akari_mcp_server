from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from typing import Any

from mcp.server.fastmcp import Context

from akari_mcp_server.server import mcp
from akari_mcp_server.tools._device_lock import oak_device_lock

_logger = logging.getLogger(__name__)

CAPTURE_DIR = "/tmp/akari_captures"
_MAX_WORKER_ERRORS = 50


def _safe_filename(filename: str) -> str:
    """ディレクトリトラバーサルを防止する。"""
    return os.path.basename(filename) or "recording.mp4"


class VideoRecorder:
    """OAK-Dカメラによるバックグラウンド動画録画を管理する。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._device: Any = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._h264_path: str = ""
        self._filepath: str = ""
        self._recording = False
        self._frame_count = 0

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def start(
        self,
        filename: str = "recording.mp4",
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> str:
        """録画を開始する。保存先パスを返す。"""
        with self._lock:
            if self._recording:
                raise RuntimeError("Already recording")

            import depthai as dai

            filename = _safe_filename(filename)
            os.makedirs(CAPTURE_DIR, exist_ok=True)

            base, ext = os.path.splitext(filename)
            self._h264_path = os.path.join(CAPTURE_DIR, base + ".h264")
            if ext.lower() in (".mp4", ""):
                self._filepath = os.path.join(CAPTURE_DIR, base + ".mp4")
            else:
                self._filepath = os.path.join(CAPTURE_DIR, filename)

            pipeline = dai.Pipeline()

            cam = pipeline.create(dai.node.ColorCamera)
            cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
            cam.setVideoSize(width, height)
            cam.setFps(fps)

            encoder = pipeline.create(dai.node.VideoEncoder)
            encoder.setDefaultProfilePreset(
                fps, dai.VideoEncoderProperties.Profile.H264_MAIN
            )

            xout = pipeline.create(dai.node.XLinkOut)
            xout.setStreamName("bitstream")

            cam.video.link(encoder.input)
            encoder.bitstream.link(xout.input)

            self._stop_event.clear()
            self._frame_count = 0

            if not oak_device_lock.acquire(blocking=False):
                raise RuntimeError(
                    "OAK-D camera is in use by another tool (e.g. camera_capture)"
                )

            try:
                self._device = dai.Device(pipeline)
                queue = self._device.getOutputQueue(
                    name="bitstream", maxSize=30, blocking=False
                )
            except Exception:
                if self._device is not None:
                    try:
                        self._device.close()
                    except Exception:
                        pass
                    self._device = None
                oak_device_lock.release()
                raise

            self._thread = threading.Thread(
                target=self._record_worker,
                args=(queue,),
                daemon=True,
            )
            self._recording = True
            self._thread.start()

            return self._filepath

    def _record_worker(self, queue: Any) -> None:
        """バックグラウンドスレッドでフレームをファイルに書き込む。"""
        error_count = 0
        try:
            with open(self._h264_path, "wb") as f:
                while not self._stop_event.is_set():
                    try:
                        data = queue.tryGet()
                        if data is not None:
                            f.write(data.getData())
                            with self._lock:
                                self._frame_count += 1
                            error_count = 0
                        else:
                            time.sleep(0.005)
                    except Exception:
                        if self._stop_event.is_set():
                            break
                        error_count += 1
                        _logger.debug("Frame read error", exc_info=True)
                        if error_count >= _MAX_WORKER_ERRORS:
                            _logger.error(
                                "Too many consecutive errors, stopping worker"
                            )
                            break
                        time.sleep(0.01)
        except Exception:
            _logger.error("Recording worker failed", exc_info=True)

    def stop(self) -> tuple[str, int]:
        """録画を停止し、(ファイルパス, フレーム数)を返す。"""
        with self._lock:
            if not self._recording:
                raise RuntimeError("Not recording")

            self._stop_event.set()

            if self._thread is not None:
                self._thread.join(timeout=5)
                if self._thread.is_alive():
                    _logger.warning("Recording worker thread did not exit in time")
                self._thread = None

            if self._device is not None:
                try:
                    self._device.close()
                except Exception:
                    _logger.debug("Error closing device", exc_info=True)
                self._device = None

            oak_device_lock.release()
            self._recording = False
            frame_count = self._frame_count

        output_path = self._convert_to_mp4()
        return output_path, frame_count

    def _convert_to_mp4(self) -> str:
        """H.264 raw bitstream をMP4に変換する。ffmpegがなければ.h264を返す。"""
        if not self._filepath.endswith(".mp4"):
            return self._h264_path

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    self._h264_path,
                    "-c",
                    "copy",
                    self._filepath,
                ],
                capture_output=True,
                timeout=30,
                check=True,
            )
            os.remove(self._h264_path)
            return self._filepath
        except (FileNotFoundError, subprocess.SubprocessError):
            _logger.warning("ffmpeg unavailable, returning raw H.264 file")
            return self._h264_path

    def cleanup(self) -> None:
        """リソースを解放する。"""
        with self._lock:
            if not self._recording:
                return
        self.stop()


def _get_recorder(ctx: Context) -> VideoRecorder:
    return ctx.request_context.lifespan_context["video_recorder"]


@mcp.tool()
def video_start_recording(
    ctx: Context,
    filename: str = "recording.mp4",
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> str:
    """OAK-Dカメラで動画の録画を開始する。停止するにはvideo_stop_recordingを呼ぶ。

    Args:
        filename: 保存ファイル名(.mp4推奨)
        width: 映像の幅(ピクセル)
        height: 映像の高さ(ピクセル)
        fps: フレームレート
    """
    try:
        recorder = _get_recorder(ctx)
        filepath = recorder.start(
            filename=filename, width=width, height=height, fps=fps
        )
        return f"Recording started. Output: {filepath}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def video_stop_recording(ctx: Context) -> str:
    """動画の録画を停止してファイルを保存する。"""
    try:
        recorder = _get_recorder(ctx)
        filepath, frame_count = recorder.stop()
        return f"Recording stopped. Saved {frame_count} frames to: {filepath}"
    except Exception as e:
        return f"Error: {e}"

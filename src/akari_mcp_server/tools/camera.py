from __future__ import annotations

import os

from mcp.server.fastmcp import Context

from akari_mcp_server.server import mcp
from akari_mcp_server.tools._device_lock import oak_device_lock

CAPTURE_DIR = "/tmp/akari_captures"


@mcp.tool()
def camera_capture(
    ctx: Context,
    filename: str = "capture.jpg",
    width: int = 1920,
    height: int = 1080,
) -> str:
    """OAK-DカメラでRGB画像を撮影して保存する。

    Args:
        filename: 保存ファイル名
        width: 画像の幅(ピクセル)
        height: 画像の高さ(ピクセル)
    """
    try:
        import cv2
        import depthai as dai

        filename = os.path.basename(filename) or "capture.jpg"
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        filepath = os.path.join(CAPTURE_DIR, filename)

        if not oak_device_lock.acquire(blocking=False):
            return "Error: OAK-D camera is in use (video recording in progress)"

        try:
            pipeline = dai.Pipeline()
            cam_rgb = pipeline.create(dai.node.ColorCamera)
            xout = pipeline.create(dai.node.XLinkOut)
            xout.setStreamName("rgb")

            cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
            cam_rgb.setPreviewSize(width, height)
            cam_rgb.setInterleaved(False)
            cam_rgb.preview.link(xout.input)

            with dai.Device(pipeline) as device:
                q = device.getOutputQueue(name="rgb", maxSize=1, blocking=True)
                frame = q.get()
                img = frame.getCvFrame()
                cv2.imwrite(filepath, img)

            return f"Image saved to: {filepath}"
        finally:
            oak_device_lock.release()
    except Exception as e:
        return f"Error: {e}"

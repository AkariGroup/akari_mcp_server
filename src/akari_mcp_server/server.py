from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    from akari_mcp_server.helpers import AkariConnectionManager
    from akari_mcp_server.tools.video import VideoRecorder

    manager = AkariConnectionManager()
    video_recorder = VideoRecorder()
    try:
        yield {"manager": manager, "video_recorder": video_recorder}
    finally:
        video_recorder.cleanup()
        manager.close()


mcp = FastMCP("akari", lifespan=lifespan)

# ツール登録（循環インポート回避のため末尾でインポート）
from akari_mcp_server.tools import camera, display, gpio, motor, video  # noqa: E402, F401


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

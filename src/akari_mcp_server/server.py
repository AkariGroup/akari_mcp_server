from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    from akari_client import AkariClient

    akari = AkariClient()
    try:
        yield {"akari": akari}
    finally:
        akari.close()


mcp = FastMCP("akari", lifespan=lifespan)

# ツール登録（循環インポート回避のため末尾でインポート）
from akari_mcp_server.tools import camera, display, gpio, motor  # noqa: E402, F401


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

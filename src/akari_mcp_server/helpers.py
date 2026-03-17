from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context

if TYPE_CHECKING:
    from akari_client import AkariClient


def get_akari(ctx: Context) -> AkariClient:
    """lifespanコンテキストからAkariClientを取得する。"""
    return ctx.request_context.lifespan_context["akari"]

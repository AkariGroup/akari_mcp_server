from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Callable, TypeVar

import grpc
from mcp.server.fastmcp import Context

if TYPE_CHECKING:
    from akari_client import AkariClient

_logger = logging.getLogger(__name__)
T = TypeVar("T")


class AkariConnectionManager:
    """AkariClientのgRPC接続管理（自動再接続付き）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._client: AkariClient | None = None
        self._connect()

    def _connect(self) -> None:
        from akari_client import AkariClient

        self._clear_channel_pool()
        self._client = AkariClient()
        _logger.info("AkariClient connected")

    def _clear_channel_pool(self) -> None:
        """channel_poolのグローバルキャッシュをクリアする。

        akari_clientのchannel_poolは閉じたチャネルを辞書に残すため、
        再接続時にクリアしないと古いチャネルが再利用される。
        """
        try:
            from akari_client.grpc import channel_pool

            with channel_pool._lock:
                channel_pool._channels.clear()
        except (ImportError, AttributeError):
            pass

    @property
    def client(self) -> AkariClient:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._connect()
        return self._client  # type: ignore[return-value]

    def reconnect(self) -> None:
        """現在の接続を破棄して再接続する。"""
        with self._lock:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    _logger.debug("Error closing old client", exc_info=True)
                self._client = None
            self._connect()

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                self._client.close()
                self._client = None


def get_akari(ctx: Context) -> AkariClient:
    """lifespanコンテキストからAkariClientを取得する。"""
    return _get_manager(ctx).client


def _get_manager(ctx: Context) -> AkariConnectionManager:
    return ctx.request_context.lifespan_context["manager"]


def call_with_retry(ctx: Context, fn: Callable[["AkariClient"], T]) -> T:
    """fn(akari)を実行し、gRPC UNAVAILABLE時に再接続して1回リトライする。"""
    manager = _get_manager(ctx)
    try:
        return fn(manager.client)
    except grpc.RpcError as e:
        if hasattr(e, "code") and e.code() == grpc.StatusCode.UNAVAILABLE:
            _logger.warning("gRPC UNAVAILABLE, attempting reconnect...")
            manager.reconnect()
            return fn(manager.client)
        raise

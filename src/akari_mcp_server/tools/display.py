from __future__ import annotations

from mcp.server.fastmcp import Context

from akari_mcp_server.helpers import get_akari
from akari_mcp_server.server import mcp


@mcp.tool()
def display_text(
    ctx: Context,
    text: str,
    pos_x: int = -999,
    pos_y: int = -999,
    size: int = 5,
    text_color_r: int = 255,
    text_color_g: int = 255,
    text_color_b: int = 255,
    back_color_r: int = 0,
    back_color_g: int = 0,
    back_color_b: int = 0,
    refresh: bool = True,
) -> str:
    """M5Stackディスプレイにテキストを表示する。

    Args:
        text: 表示する文字列
        pos_x: X位置(0-320)。-999で中央揃え
        pos_y: Y位置(0-240)。-999で中央揃え
        size: 文字サイズ(1-11)
        text_color_r: 文字色R(0-255)
        text_color_g: 文字色G(0-255)
        text_color_b: 文字色B(0-255)
        back_color_r: 背景色R(0-255)
        back_color_g: 背景色G(0-255)
        back_color_b: 背景色B(0-255)
        refresh: 画面全体を更新するか
    """
    try:
        from akari_client.color import Color

        akari = get_akari(ctx)
        text_color = Color(red=text_color_r, green=text_color_g, blue=text_color_b)
        back_color = Color(red=back_color_r, green=back_color_g, blue=back_color_b)
        akari.m5stack.set_display_text(
            text,
            pos_x=pos_x,
            pos_y=pos_y,
            size=size,
            text_color=text_color,
            back_color=back_color,
            refresh=refresh,
        )
        return f"Displayed text: '{text}'"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def display_color(
    ctx: Context,
    r: int = 0,
    g: int = 0,
    b: int = 0,
) -> str:
    """M5Stackディスプレイの背景色を設定する。

    Args:
        r: 赤(0-255)
        g: 緑(0-255)
        b: 青(0-255)
    """
    try:
        from akari_client.color import Color

        akari = get_akari(ctx)
        akari.m5stack.set_display_color(Color(red=r, green=g, blue=b))
        return f"Display color set to: r={r}, g={g}, b={b}"
    except Exception as e:
        return f"Error: {e}"

from __future__ import annotations

from mcp.server.fastmcp import Context

from akari_mcp_server.helpers import call_with_retry
from akari_mcp_server.server import mcp


@mcp.tool()
def gpio_set_dout(ctx: Context, pin_id: int, value: bool) -> str:
    """デジタル出力を設定する。

    Args:
        pin_id: ピン番号(0または1)
        value: 出力値(TrueでHi 3.3V、FalseでLo 0V)
    """
    try:

        def _do(akari):
            akari.m5stack.set_dout(pin_id, value)
            return f"dout{pin_id} set to {value}"

        return call_with_retry(ctx, _do)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def gpio_set_pwmout(ctx: Context, pin_id: int, value: int) -> str:
    """PWM出力を設定する。

    Args:
        pin_id: ピン番号(0)
        value: PWM値(0-255、0で0V、255で3.3V)
    """
    try:

        def _do(akari):
            akari.m5stack.set_pwmout(pin_id, value)
            return f"pwmout{pin_id} set to {value}"

        return call_with_retry(ctx, _do)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def gpio_set_allout(
    ctx: Context,
    dout0: bool | None = None,
    dout1: bool | None = None,
    pwmout0: int | None = None,
) -> str:
    """全GPIO出力をまとめて設定する。

    Args:
        dout0: dout0の出力値
        dout1: dout1の出力値
        pwmout0: pwmout0のPWM値(0-255)
    """
    try:

        def _do(akari):
            akari.m5stack.set_allout(dout0=dout0, dout1=dout1, pwmout0=pwmout0)
            return f"All outputs set: dout0={dout0}, dout1={dout1}, pwmout0={pwmout0}"

        return call_with_retry(ctx, _do)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def gpio_reset(ctx: Context) -> str:
    """全GPIO出力を初期値にリセットする(dout0=False, dout1=False, pwmout0=0)。"""
    try:

        def _do(akari):
            akari.m5stack.reset_allout()
            return "All GPIO outputs reset to defaults"

        return call_with_retry(ctx, _do)
    except Exception as e:
        return f"Error: {e}"

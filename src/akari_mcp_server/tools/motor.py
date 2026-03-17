from __future__ import annotations

from mcp.server.fastmcp import Context

from akari_mcp_server.helpers import get_akari
from akari_mcp_server.server import mcp


@mcp.tool()
def motor_enable_servo(ctx: Context, pan: bool = True, tilt: bool = True) -> str:
    """サーボモータを有効化する。

    Args:
        pan: pan軸を有効化するか
        tilt: tilt軸を有効化するか
    """
    try:
        akari = get_akari(ctx)
        akari.joints.set_servo_enabled(
            pan=True if pan else None, tilt=True if tilt else None
        )
        return f"Servo enabled: pan={pan}, tilt={tilt}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def motor_disable_servo(ctx: Context, pan: bool = True, tilt: bool = True) -> str:
    """サーボモータを無効化する。

    Args:
        pan: pan軸を無効化するか
        tilt: tilt軸を無効化するか
    """
    try:
        akari = get_akari(ctx)
        akari.joints.set_servo_enabled(
            pan=False if pan else None, tilt=False if tilt else None
        )
        return f"Servo disabled: pan={pan}, tilt={tilt}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def motor_move(
    ctx: Context,
    pan: float | None = None,
    tilt: float | None = None,
    sync: bool = True,
) -> str:
    """モータを指定角度[rad]に移動する。

    Args:
        pan: pan軸の目標角度[rad]
        tilt: tilt軸の目標角度[rad]
        sync: Trueなら移動完了まで待機
    """
    try:
        akari = get_akari(ctx)
        akari.joints.move_joint_positions(pan=pan, tilt=tilt, sync=sync)
        return f"Moved to: pan={pan}, tilt={tilt}, sync={sync}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def motor_get_positions(ctx: Context) -> str:
    """モータの現在角度[rad]を取得する。"""
    try:
        akari = get_akari(ctx)
        positions = akari.joints.get_joint_positions()
        return f"Positions: pan={positions['pan']:.4f}, tilt={positions['tilt']:.4f}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def motor_set_velocities(
    ctx: Context,
    pan: float | None = None,
    tilt: float | None = None,
) -> str:
    """モータの目標速度[rad/s]を設定する。

    Args:
        pan: pan軸の目標速度[rad/s]
        tilt: tilt軸の目標速度[rad/s]
    """
    try:
        akari = get_akari(ctx)
        akari.joints.set_joint_velocities(pan=pan, tilt=tilt)
        return f"Velocities set: pan={pan}, tilt={tilt}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def motor_set_accelerations(
    ctx: Context,
    pan: float | None = None,
    tilt: float | None = None,
) -> str:
    """モータの目標加速度[rad/s²]を設定する。

    Args:
        pan: pan軸の目標加速度[rad/s²]
        tilt: tilt軸の目標加速度[rad/s²]
    """
    try:
        akari = get_akari(ctx)
        akari.joints.set_joint_accelerations(pan=pan, tilt=tilt)
        return f"Accelerations set: pan={pan}, tilt={tilt}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def motor_get_limits(ctx: Context) -> str:
    """モータの関節リミット[rad]を取得する。"""
    try:
        akari = get_akari(ctx)
        limits = akari.joints.get_joint_limits()
        parts = []
        for name, limit in limits.items():
            parts.append(f"{name}: min={limit.min:.4f}, max={limit.max:.4f}")
        return "Limits: " + "; ".join(parts)
    except Exception as e:
        return f"Error: {e}"

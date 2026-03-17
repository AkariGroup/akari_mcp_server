"""OAK-Dカメラの排他アクセスを管理するプロセスワイドロック。"""

from __future__ import annotations

import threading

oak_device_lock = threading.Lock()

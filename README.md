# AKARI MCP Server

AKARIロボットをClaude Codeから操作するためのMCP (Model Context Protocol) サーバー。

## 機能

| カテゴリ | ツール | 説明 |
|---------|--------|------|
| モータ | `motor_enable_servo` | サーボ有効化 |
| | `motor_disable_servo` | サーボ無効化 |
| | `motor_move` | 指定角度[rad]に移動 |
| | `motor_get_positions` | 現在角度取得 |
| | `motor_set_velocities` | 目標速度[rad/s]設定 |
| | `motor_set_accelerations` | 目標加速度[rad/s²]設定 |
| | `motor_get_limits` | 関節リミット取得 |
| 画面 | `display_text` | M5Stackにテキスト表示 |
| | `display_color` | M5Stack背景色設定 |
| カメラ | `camera_capture` | OAK-DカメラでRGB撮影 |
| GPIO | `gpio_set_dout` | デジタル出力設定 |
| | `gpio_set_pwmout` | PWM出力設定(0-255) |
| | `gpio_set_allout` | 全出力同時設定 |
| | `gpio_reset` | 全出力リセット |

## セットアップ

### 方法A: uvxでGitHubから直接インストール（推奨）

`~/.claude.json` の `mcpServers` に以下を追加:

```json
"akari": {
  "type": "stdio",
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/AkariGroup/akari_mcp_server",
    "akari-mcp-server"
  ]
}
```

### 方法B: ローカルリポジトリから実行

```bash
git clone https://github.com/AkariGroup/akari_mcp_server.git
cd akari_mcp_server
uv sync
```

`~/.claude.json` の `mcpServers` に以下を追加:

```json
"akari": {
  "type": "stdio",
  "command": "uv",
  "args": [
    "--directory",
    "/path/to/akari_mcp_server",
    "run",
    "akari-mcp-server"
  ]
}
```

### Claude Codeを再起動

MCPサーバーはClaude Code起動時に読み込まれるため、設定変更後は再起動が必要。

## 使い方（Claude Codeから）

Claude Codeで自然言語で指示するだけでAKARIを操作できる:

```
「AKARIのサーボを有効にして、pan=0.5, tilt=-0.3に動かして」
「M5Stackの画面を赤くして」
「カメラで写真を撮って」
「GPIO出力をリセットして」
```

## 動作確認

```bash
# サーバー単体起動テスト
uv run akari-mcp-server
```

AKARI実機未接続の場合、joint/m5stackのWARNINGが出るが正常。

## 依存関係

- `mcp[cli]` - MCP Python SDK
- `akari-client[grpc]` - AKARI Python SDK
- `depthai` - OAK-Dカメラ制御
- `opencv-python` - 画像処理

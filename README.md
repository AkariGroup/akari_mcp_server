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
| | `video_start_recording` | 動画の録画開始 |
| | `video_stop_recording` | 動画の録画停止・保存 |
| GPIO | `gpio_set_dout` | デジタル出力設定 |
| | `gpio_set_pwmout` | PWM出力設定(0-255) |
| | `gpio_set_allout` | 全出力同時設定 |
| | `gpio_reset` | 全出力リセット |

## セットアップ

### Claude Codeに登録

```bash
claude mcp add akari -- uvx --from git+https://github.com/AkariGroup/akari_mcp_server akari-mcp-server
```

Claude Codeを再起動すると使えるようになる。

### ローカル開発用

```bash
git clone https://github.com/AkariGroup/akari_mcp_server.git
cd akari_mcp_server
uv sync
```

```bash
claude mcp add akari -- uv --directory /path/to/akari_mcp_server run akari-mcp-server
```

## 使い方（Claude Codeから）

Claude Codeで自然言語で指示するだけでAKARIを操作できる:

```
「AKARIのサーボを有効にして、pan=0.5, tilt=-0.3に動かして」
「M5Stackの画面を赤くして」
「カメラで写真を撮って」
「動画を撮影開始して」→（しばらく後）→「録画を停止して」
「GPIO出力をリセットして」
```

## 動作確認

```bash
# サーバー単体起動テスト
uv run akari-mcp-server
```

AKARI実機未接続の場合、joint/m5stackのWARNINGが出るが正常。

## 注意事項

- OAK-Dカメラは排他リソース。動画録画中は`camera_capture`は使用不可（録画停止後に使用可能）
- 動画録画にはH.264エンコードを使用。`ffmpeg`がインストールされていればMP4に自動変換、なければ`.h264`ファイルで保存
- 録画ファイルは`/tmp/akari_captures/`に保存される

## VOICEVOX音声出力（オプション）

Claude Codeの応答をVOICEVOXで音声合成して読み上げる機能。hookスクリプトは `.claude/hooks/voicevox_speak.sh` に同梱されている。

### 前提条件

- `jq` - JSON処理
- `curl` - HTTP通信
- 音声再生コマンド: `paplay`(PulseAudio), `aplay`(ALSA), `ffplay`(ffmpeg), `play`(sox) のいずれか

```bash
# Ubuntu/Debianの場合
sudo apt install jq curl alsa-utils
```

### VOICEVOX エンジンのセットアップ（Docker CPU版）

```bash
# イメージ取得
docker pull voicevox/voicevox_engine:cpu-latest

# 起動（バックグラウンド、名前付き、自動再起動あり）
docker run -d --name voicevox --restart unless-stopped -p '127.0.0.1:50021:50021' voicevox/voicevox_engine:cpu-latest

# 起動確認
curl http://127.0.0.1:50021/version

# 停止する場合
docker stop voicevox
```

NVIDIA GPU搭載の場合は `nvidia-latest` タグを使うと高速化できる:

```bash
docker run -d --name voicevox --restart unless-stopped --gpus all -p '127.0.0.1:50021:50021' voicevox/voicevox_engine:nvidia-latest
```

### Claude Code hookの有効化

`.claude/settings.local.json` を作成して hook を登録する:

```bash
cat > .claude/settings.local.json << 'EOF'
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/voicevox_speak.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
EOF
```

Claude Codeを再起動すると、応答のたびにVOICEVOXで読み上げが行われる。

### カスタマイズ（環境変数）

| 環境変数 | デフォルト | 説明 |
|----------|-----------|------|
| `VOICEVOX_HOST` | `http://127.0.0.1:50021` | VOICEVOXエンジンのURL |
| `VOICEVOX_SPEAKER` | `3` (ずんだもん・ノーマル) | 話者ID |
| `VOICEVOX_MAX_LENGTH` | `200` | 読み上げ最大文字数 |
| `VOICEVOX_SPEED` | `1.2` | 話速（1.0=標準） |

話者IDの一覧は `curl http://127.0.0.1:50021/speakers | jq` で確認できる。

主な話者ID例:

| ID | 話者 |
|----|------|
| 2 | 四国めたん（ノーマル） |
| 3 | ずんだもん（ノーマル） |
| 8 | 春日部つむぎ |
| 13 | 青山龍星 |
| 46 | 小夜/SAYO |

## 依存関係

- `mcp[cli]` - MCP Python SDK
- `akari-client[grpc]` - AKARI Python SDK
- `depthai` - OAK-Dカメラ制御
- `opencv-python` - 画像処理
- `ffmpeg` (オプション) - H.264→MP4変換

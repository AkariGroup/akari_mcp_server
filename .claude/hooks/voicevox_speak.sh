#!/bin/bash
# voicevox_speak.sh - Claude Codeの出力をVOICEVOXで音声合成して読み上げるhook
#
# Stop hookとして使用。Claudeの応答完了時に最後のメッセージを読み上げる。
# 必要: jq, curl, aplay/paplay/ffplay のいずれか
#
# 環境変数:
#   VOICEVOX_HOST       - VOICEVOXエンジンURL (default: http://127.0.0.1:50021)
#   VOICEVOX_SPEAKER    - 話者ID (default: 3 = ずんだもん・ノーマル)
#   VOICEVOX_MAX_LENGTH - 読み上げ最大文字数 (default: 200)
#   VOICEVOX_SPEED      - 話速 (default: 1.2)

set -euo pipefail

# 依存コマンドチェック
for cmd in jq curl; do
    if ! command -v "$cmd" &>/dev/null; then
        exit 0
    fi
done

VOICEVOX_HOST="${VOICEVOX_HOST:-http://127.0.0.1:50021}"
VOICEVOX_SPEAKER="${VOICEVOX_SPEAKER:-3}"
MAX_LENGTH="${VOICEVOX_MAX_LENGTH:-200}"
SPEED="${VOICEVOX_SPEED:-1.2}"

# 環境変数バリデーション
if ! [[ "$VOICEVOX_SPEAKER" =~ ^[0-9]+$ ]]; then
    exit 0
fi
if ! [[ "$MAX_LENGTH" =~ ^[0-9]+$ ]]; then
    exit 0
fi
if ! [[ "$SPEED" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    exit 0
fi

# stdinからhookデータ(JSON)を読み取る
INPUT=$(cat)

# stop_hook_activeがtrueの場合はスキップ（ループ防止）
STOP_HOOK_ACTIVE=$(jq -r '.stop_hook_active // false' <<< "$INPUT")
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
    exit 0
fi

# transcript_pathを取得
TRANSCRIPT_PATH=$(jq -r '.transcript_path // empty' <<< "$INPUT")
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# VOICEVOXが起動しているか確認
if ! curl -s --max-time 1 "${VOICEVOX_HOST}/version" > /dev/null 2>&1; then
    exit 0
fi

# transcriptから最後のassistantメッセージのテキストを抽出
# transcript.jsonlはNDJSON形式
TEXT=$(tac "$TRANSCRIPT_PATH" | while IFS= read -r line; do
    ROLE=$(jq -r '.role // empty' <<< "$line" 2>/dev/null)
    if [ "$ROLE" = "assistant" ]; then
        jq -r '
            [.content[] | select(.type == "text") | .text] | join(" ")
        ' <<< "$line" 2>/dev/null
        break
    fi
done)

if [ -z "$TEXT" ]; then
    exit 0
fi

# マークダウン記法を除去（複数行コードブロック対応）
TEXT=$(printf '%s\n' "$TEXT" | sed '/^```/,/^```/d' | sed -E \
    -e 's/`[^`]*`//g' \
    -e 's/^#+[[:space:]]*//g' \
    -e 's/\*\*([^*]*)\*\*/\1/g' \
    -e 's/\*([^*]*)\*/\1/g' \
    -e 's/\[([^]]*)\]\([^)]*\)/\1/g' \
    -e 's/^[[:space:]]*[-*][[:space:]]*//' \
    -e 's/^[[:space:]]*[0-9]+\.[[:space:]]*//')

# 空白をトリム
TEXT=$(printf '%s' "$TEXT" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

if [ -z "$TEXT" ]; then
    exit 0
fi

# テキストを切り詰める
if [ "${#TEXT}" -gt "$MAX_LENGTH" ]; then
    TEXT="${TEXT:0:$MAX_LENGTH}。以下省略"
fi

# 一時ファイル
TMPFILE=$(mktemp /tmp/voicevox_XXXXXX.wav)

# バックグラウンドで音声合成・再生を実行
(
    cleanup() { rm -f "$TMPFILE"; }
    trap cleanup EXIT

    # Step 1: audio_query
    # VOICEVOX APIはtextをクエリパラメータとして受け取るPOSTエンドポイント
    # --get: --data-urlencodeのデータをURLクエリパラメータに変換
    # -X POST: メソッドをPOSTに強制
    QUERY=$(curl -s --max-time 10 -X POST \
        "${VOICEVOX_HOST}/audio_query?speaker=${VOICEVOX_SPEAKER}" \
        --get --data-urlencode "text=${TEXT}" 2>/dev/null)

    if [ -z "$QUERY" ]; then
        exit 0
    fi

    # 話速を調整（--argjsonでインジェクション防止）
    QUERY=$(jq --argjson speed "$SPEED" '.speedScale = $speed' <<< "$QUERY")

    # Step 2: synthesis
    curl -s --max-time 30 -X POST \
        "${VOICEVOX_HOST}/synthesis?speaker=${VOICEVOX_SPEAKER}" \
        -H "Content-Type: application/json" \
        -d "$QUERY" \
        -o "$TMPFILE" 2>/dev/null

    if [ ! -s "$TMPFILE" ]; then
        exit 0
    fi

    # 音声再生（利用可能なプレーヤーを自動検出）
    if command -v paplay &>/dev/null; then
        paplay "$TMPFILE" 2>/dev/null
    elif command -v aplay &>/dev/null; then
        aplay -q "$TMPFILE" 2>/dev/null
    elif command -v ffplay &>/dev/null; then
        ffplay -nodisp -autoexit "$TMPFILE" 2>/dev/null
    elif command -v play &>/dev/null; then
        play -q "$TMPFILE" 2>/dev/null
    fi
) &
disown

exit 0

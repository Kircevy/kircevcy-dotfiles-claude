# Provider shortcuts. Source this *after* integration.sh if you have one or
# more of the corresponding API keys set in your environment:
#   ZAI_API_KEY        → glm     (Zhipu BigModel)
#   DEEPSEEK_API_KEY   → deepseek
#   OPENROUTER_API_KEY → openrouter
#   OFOX_API_KEY       → ofox    (OfoxAI aggregator, Gemini 3.1 pro)
#   LLAMA_API_KEY      → qwen
#   (none)             → gpt     (ChatGPT OAuth — needs the codex-to-claude
#                                 proxy running locally; see
#                                 https://github.com/archibate/codex-to-claude)
#
# Each shortcut routes claude through ~/.claude/providers/<name>.json which
# rebinds ANTHROPIC_BASE_URL and the haiku/sonnet/opus model aliases to the
# provider's catalog.

claude-with() {
    local provider="$1"
    shift
    local token
    case "$provider" in
        glm)
            token="$ZAI_API_KEY"
            ;;
        deepseek)
            if [ -z "${DEEPSEEK_API_KEY:-}" ] && [ -f ~/.claude/proxy/.env ]; then
                . ~/.claude/proxy/.env
            fi
            token="${DEEPSEEK_API_KEY:-}"
            ;;
        deepseek-v4)
            # proxy 不校验 key，传占位符即可
            token="dummy"
            ;;
        deepseek-free)
            # zen 免费模型走本地转换代理，不校验 key
            token="dummy"
            ;;
        deepseek-go)
            # go 计划模型走本地转换代理，key 由代理读取
            token="dummy"
            ;;
        deepseek-vision)
            # 识图代理不校验 key，传占位符即可
            token="dummy"
            ;;
        openrouter)
            token="$OPENROUTER_API_KEY"
            ;;
        ofox)
            token="$OFOX_API_KEY"
            ;;
        qwen)
            token="$LLAMA_API_KEY"
            ;;
        gpt)
            # codex-to-claude proxy: ChatGPT OAuth backend, no real token needed.
            token="dummy"
            ;;
        longcat)
            # key 从本地 longcat.json 读取（未跟踪），不写入仓库
            token="$(jq -r '.env.ANTHROPIC_AUTH_TOKEN // ""' ~/.claude/providers/longcat.json)"
            ;;
        kimi)
            # key 硬编码在 json 里，不需要环境变量
            token="embedded"
            ;;
        agnes)
            if [ -z "${AGNES_API_KEY:-}" ] && [ -f ~/.claude/proxy/.env ]; then
                . ~/.claude/proxy/.env
            fi
            token="${AGNES_API_KEY:-}"
            ;;
        *)
            echo "claude-with: unknown provider '$provider'" >&2
            return 1
            ;;
    esac
    if [ -n "$token" ]; then
        ANTHROPIC_AUTH_TOKEN="$token" claude --settings ~/.claude/providers/"$provider".json "$@"
    else
        unset ANTHROPIC_AUTH_TOKEN
        claude --settings ~/.claude/providers/"$provider".json "$@"
    fi
}

glm() {
    claude-with glm "$@"
}

deepseek() {
    claude-with deepseek "$@"
}

deepseek-v4() {
    claude-with deepseek-v4 "$@"
}

deepseek-free() {
    local port=8765
    if ! curl -s -m 2 "http://127.0.0.1:$port/health" >/dev/null; then
        setsid nohup python3 ~/.claude/proxy/deepseek-zen-proxy.py "$port" >/tmp/deepseek-zen-proxy.log 2>&1 &
        for _ in $(seq 1 20); do
            curl -s -m 1 "http://127.0.0.1:$port/health" >/dev/null && break
            sleep 0.3
        done
    fi
    claude-with deepseek-free "$@"
}

deepseek-go() {
    local port=18085
    if ! curl -s -m 2 "http://127.0.0.1:$port/health" >/dev/null; then
        setsid nohup python3 ~/.claude/proxy/deepseek-go-proxy.py "$port" >/tmp/deepseek-go-proxy.log 2>&1 &
        for _ in $(seq 1 20); do
            curl -s -m 1 "http://127.0.0.1:$port/health" >/dev/null && break
            sleep 0.3
        done
    fi
    claude-with deepseek-go "$@"
}

deepseek-vision() {
    # 识图代理：图片经 Kimi 描述后转发 DeepSeek，key 从 provider json 读取
    local port=8081
    if ! curl -s -m 2 "http://127.0.0.1:$port/health" >/dev/null; then
        local ds_key kimi_key
        ds_key="$(jq -r '.env.ANTHROPIC_API_KEY' ~/.claude/providers/deepseek.json)"
        kimi_key="$(jq -r '.env.ANTHROPIC_API_KEY' ~/.claude/providers/kimi.json)"
        setsid nohup env DEEPSEEK_API_KEY="$ds_key" KIMI_API_KEY="$kimi_key" \
            KIMI_BASE_URL="https://api.kimi.com/coding/v1" \
            uv run --project /home/wgz/deepseek-vision-proxy -m deepseek_vision_proxy \
            >/tmp/deepseek-vision-proxy.log 2>&1 &
        for _ in $(seq 1 20); do
            curl -s -m 1 "http://127.0.0.1:$port/health" >/dev/null && break
            sleep 0.3
        done
    fi
    claude-with deepseek-vision "$@"
}

openrouter() {
    claude-with openrouter "$@"
}

ofox() {
    claude-with ofox "$@"
}

qwen() {
    claude-with qwen "$@"
}

gpt() {
    claude-with gpt "$@"
}

agnes() {
    claude-with agnes "$@"
}

longcat() {
    claude-with longcat "$@"
}

kimi() {
    claude-with kimi "$@"
}

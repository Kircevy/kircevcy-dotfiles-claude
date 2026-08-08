# Provider shortcuts. Source this *after* integration.fish if you have one or
# more of the corresponding API keys set in your environment:
#   ZAI_API_KEY        → glm     (Zhipu BigModel)
#   DEEPSEEK_API_KEY   → deepseek
#   OPENROUTER_API_KEY → openrouter
#   OFOX_API_KEY       → ofox    (OfoxAI aggregator, Gemini 3.1 pro
#   LLAMA_API_KEY      → qwen
#   (none)             → gpt     (ChatGPT OAuth — needs the codex-to-claude
#                                 proxy running locally; see
#                                 https://github.com/archibate/codex-to-claude)
#
# Each shortcut routes claude through ~/.claude/providers/<name>.json which
# rebinds ANTHROPIC_BASE_URL and the haiku/sonnet/opus model aliases to the
# provider's catalog.

function claude-with
    set -l provider $argv[1]
    switch $provider
        case glm
            set -fx ANTHROPIC_AUTH_TOKEN $ZAI_API_KEY
        case deepseek
            if not set -q DEEPSEEK_API_KEY
                and test -f ~/.claude/proxy/.env
                set -fx DEEPSEEK_API_KEY (string replace -r '^DEEPSEEK_API_KEY=' '' -- (grep '^DEEPSEEK_API_KEY=' ~/.claude/proxy/.env 2>/dev/null))
            end
            set -fx ANTHROPIC_AUTH_TOKEN $DEEPSEEK_API_KEY
        case deepseek-v4
            # token 硬编码在 json 里，不需要环境变量
            set -fx ANTHROPIC_AUTH_TOKEN embedded
        case deepseek-free
            # zen 免费模型走本地转换代理，不校验 key
            set -fx ANTHROPIC_AUTH_TOKEN embedded
        case deepseek-go
            # go 计划模型走本地转换代理，key 由代理读取
            set -fx ANTHROPIC_AUTH_TOKEN embedded
        case deepseek-vision
            # 识图代理不校验 key，传占位符即可
            set -fx ANTHROPIC_AUTH_TOKEN embedded
        case openrouter
            set -fx ANTHROPIC_AUTH_TOKEN $OPENROUTER_API_KEY
        case ofox
            set -fx ANTHROPIC_AUTH_TOKEN $OFOX_API_KEY
        case qwen
            set -fx ANTHROPIC_AUTH_TOKEN $LLAMA_API_KEY
        case gpt
            # codex-to-claude proxy: ChatGPT OAuth backend, no real token needed.
            set -fx ANTHROPIC_AUTH_TOKEN dummy
        case kimi
            # key 硬编码在 json 里，不需要环境变量
            set -fx ANTHROPIC_AUTH_TOKEN embedded
        case longcat
            # key 从本地 longcat.json 读取（未跟踪），不写入仓库
            set -fx ANTHROPIC_AUTH_TOKEN (jq -r '.env.ANTHROPIC_AUTH_TOKEN // ""' ~/.claude/providers/longcat.json)
        case agnes
            if set -q AGNES_API_KEY
                set -fx ANTHROPIC_AUTH_TOKEN $AGNES_API_KEY
            end
        case '*'
            echo "claude-with: unknown provider '$provider'" >&2
            return 1
    end
    claude --settings ~/.claude/providers/$provider.json $argv[2..]
end

function glm
    claude-with glm $argv
end

function deepseek
    claude-with deepseek $argv
end

function openrouter
    claude-with openrouter $argv
end

function ofox
    claude-with ofox $argv
end

function qwen
    claude-with qwen $argv
end

function gpt
    claude-with gpt $argv
end

function agnes
    claude-with agnes $argv
end

function longcat
    claude-with longcat $argv
end

function kimi
    claude-with kimi $argv
end

function deepseek-v4
    # Start proxy if not running (disown to survive terminal close)
    if not lsof -i :8080 >/dev/null 2>&1
        uv run --script ~/.claude/proxy/deepseek-v4-proxy.py &
        disown
        sleep 2
    end
    claude-with deepseek-v4 $argv
end

function deepseek-free
    if not curl -s -m 2 http://127.0.0.1:8765/health >/dev/null
        python3 ~/.claude/proxy/deepseek-zen-proxy.py 8765 &
        disown
        for _ in (seq 20)
            curl -s -m 1 http://127.0.0.1:8765/health >/dev/null; and break
            sleep 0.3
        end
    end
    claude-with deepseek-free $argv
end

function deepseek-go
    if not curl -s -m 2 http://127.0.0.1:18085/health >/dev/null
        python3 ~/.claude/proxy/deepseek-go-proxy.py 18085 &
        disown
        for _ in (seq 20)
            curl -s -m 1 http://127.0.0.1:18085/health >/dev/null; and break
            sleep 0.3
        end
    end
    claude-with deepseek-go $argv
end

function deepseek-vision
    # 识图代理：图片经 Kimi 描述后转发 DeepSeek，key 从 provider json 读取
    set -l port 8081
    if not curl -s -m 2 "http://127.0.0.1:$port/health" >/dev/null
        set -l ds_key (jq -r '.env.ANTHROPIC_API_KEY' ~/.claude/providers/deepseek.json)
        set -l kimi_key (jq -r '.env.ANTHROPIC_API_KEY' ~/.claude/providers/kimi.json)
        env DEEPSEEK_API_KEY="$ds_key" KIMI_API_KEY="$kimi_key" \
            KIMI_BASE_URL="https://api.kimi.com/coding/v1" \
            uv run --project /home/wgz/deepseek-vision-proxy -m deepseek_vision_proxy \
            >/tmp/deepseek-vision-proxy.log 2>&1 &
        disown
        for _ in (seq 1 20)
            curl -s -m 1 "http://127.0.0.1:$port/health" >/dev/null; and break
            sleep 0.3
        end
    end
    claude-with deepseek-vision $argv
end

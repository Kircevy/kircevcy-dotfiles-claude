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
            set -fx ANTHROPIC_AUTH_TOKEN $DEEPSEEK_API_KEY
        case deepseek-v4
            # token 硬编码在 json 里，不需要环境变量
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
        case longcat
            set -fx ANTHROPIC_AUTH_TOKEN REDACTED
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

function deepseek-v4
    # Start proxy if not running (disown to survive terminal close)
    if not lsof -i :8080 >/dev/null 2>&1
        uv run --script ~/.claude/proxy/deepseek-v4-proxy.py &
        disown
        sleep 2
    end
    claude-with deepseek-v4 $argv
end

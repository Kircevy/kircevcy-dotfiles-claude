# deepseek-go provider (keyless setup)

Run OpenCode's paid **go-plan** models (e.g. `deepseek-v4-flash`, `deepseek-v4-pro[1m]`)
inside Claude Code via a local Anthropic→OpenAI translation proxy.

## What you need (your own, never shared)

1. **An OpenCode subscription** that includes the `opencode-go` provider. Your key is
   personal — do not commit or share it.
2. **Network access to `opencode.ai`**. If it is blocked from your machine, use your
   own VPN / clash / proxy. This repo cannot give you one.
3. Python 3 (stdlib only for the proxy; no pip installs).

## Setup

```bash
# 1. point Claude Code at this repo's config (or copy providers/, proxy/ into ~/.claude)
# 2. provide your own go key — either env var or opencode's auth file:
export OPENCODE_GO_API_KEY=sk-....            # your opencode-go key
#    (fallback: the proxy reads ~/.local/share/opencode/auth.json -> provider "opencode-go")

# 3. load the provider shortcuts (bash):
source ~/.claude/integration-providers.sh
#    (fish: source ~/.claude/integration-providers.fish)

# 4. launch
deepseek-go
```

`deepseek-go` auto-starts the translation proxy on `127.0.0.1:18085` if it isn't
already running, then starts Claude Code with `providers/deepseek-go.json`.

## How it works

`proxy/deepseek-go-proxy.py` translates the Anthropic Messages protocol to OpenAI
`chat/completions` and forwards to `https://opencode.ai/zen/go/v1/chat/completions`.
No key is stored in this repo — everything comes from your environment.

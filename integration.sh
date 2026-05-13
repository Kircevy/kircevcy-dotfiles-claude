claude() {
    local _session
    _session="$(basename "$PWD")-$(openssl rand -hex 8 2>/dev/null || printf '%05x%05x' $RANDOM $RANDOM)"
    SHELL="$(command -v bash)" \
    PYTHONUNBUFFERED=1 \
    AGENT_BROWSER_SESSION="$_session" \
    command claude --thinking-display summarized --allow-dangerously-skip-permissions "$@"
}

claude-simple() {
    if [ $# -eq 0 ]; then
        CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1 claude
    else
        CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1 "$@"
    fi
}

opus() {
    claude --model opus "$@"
}

opusplan() {
    claude --model opusplan --permission-mode plan "$@"
}

sonnet() {
    claude --model sonnet "$@"
}

haiku() {
    claude --model haiku "$@"
}

hai() {
    CLAUDE_CODE_EXTRA_BODY='{"temperature":0}' \
    CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1 \
    CLAUDE_CODE_DISABLE_POLICY_SKILLS=1 \
    CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
    ENABLE_CLAUDEAI_MCP_SERVERS=false \
    CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1 \
    AUDIT_BACKEND=none \
    claude --model haiku --permission-mode default --thinking disabled "$@"
}

commit() {
    if command -v gitleaks >/dev/null 2>&1; then
        if ! gitleaks detect --no-banner; then
            echo "gitleaks detected secrets, aborting commit" >&2
            return 1
        fi
    fi
    local extra=""
    if [ $# -gt 0 ]; then
        extra=" Additional user note to help you understand: $*"
    fi
    CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1 \
    CLAUDE_CODE_DISABLE_POLICY_SKILLS=1 \
    CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
    ENABLE_CLAUDEAI_MCP_SERVERS=false \
    CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1 \
    AUDIT_BACKEND=none \
    timeout -v -s INT 80s claude -p --model haiku --max-turns 50 \
        --permission-mode dontAsk \
        --allowedTools "Bash(git add:*),Bash(git commit:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git ls-files:*),Bash(rg:*),Bash(fd:*),Bash(gitleaks:*),Bash(exa:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(tail:*),Bash(wc:*),Bash(file:*),Bash(jq:*),Bash(stat:*),Bash(tree:*),Bash(pwd),Bash(which:*),Read,Edit,Write,Grep,Glob" \
        "Make a git commit with commit message briefly describing what changed in the codebase. Stage and commit all changed files (including untracked ones). If some stagable files looks like should appear in .gitignore, add the file name pattern to .gitignore before stage. Do not edit files in this conversation.${extra}"
}

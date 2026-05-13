function claude
    set -lx SHELL (command -v bash)
    set -lx PYTHONUNBUFFERED 1
    set -lx AGENT_BROWSER_SESSION (basename $PWD)-(command -sq openssl; and openssl rand -hex 8; or random)
    command claude --thinking-display summarized --allow-dangerously-skip-permissions $argv
end

function claude-simple
    set -lx CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT 1
    if test (count $argv) -eq 0
        claude
    else
        $argv
    end
end

function opus
    claude --model opus $argv
end

function opusplan
    claude --model opusplan --permission-mode plan $argv
end

function sonnet
    claude --model sonnet $argv
end

function haiku
    claude --model haiku $argv
end

function hai
    set -lx CLAUDE_CODE_EXTRA_BODY '{"temperature":0}'
    set -lx CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT 1
    set -lx CLAUDE_CODE_DISABLE_POLICY_SKILLS 1
    set -lx CLAUDE_CODE_DISABLE_AUTO_MEMORY 1
    set -lx ENABLE_CLAUDEAI_MCP_SERVERS false
    set -lx CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY 1
    set -lx AUDIT_BACKEND none
    claude --model haiku --permission-mode default --thinking disabled $argv
end

function commit
    if command -sq gitleaks
        if not gitleaks detect --no-banner
            echo "gitleaks detected secrets, aborting commit" >&2
            return 1
        end
    end
    set -l extra ""
    if set -q argv[1]
        set extra " Additional user note to help you understand: $argv"
    end
    set -lx CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT 1
    set -lx CLAUDE_CODE_DISABLE_POLICY_SKILLS 1
    set -lx CLAUDE_CODE_DISABLE_AUTO_MEMORY 1
    set -lx ENABLE_CLAUDEAI_MCP_SERVERS false
    set -lx CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY 1
    set -lx AUDIT_BACKEND none
    timeout -v -s INT 80s claude -p --model haiku --max-turns 50 \
        --permission-mode dontAsk \
        --allowedTools "Bash(git add:*),Bash(git commit:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git ls-files:*),Bash(rg:*),Bash(fd:*),Bash(gitleaks:*),Bash(exa:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(tail:*),Bash(wc:*),Bash(file:*),Bash(jq:*),Bash(stat:*),Bash(tree:*),Bash(pwd),Bash(which:*),Read,Edit,Write,Grep,Glob" \
        "Make a git commit with commit message briefly describing what changed in the codebase. Stage and commit all changed files (including untracked ones). If some stagable files looks like should appear in .gitignore, add the file name pattern to .gitignore before stage. Do not edit files in this conversation.$extra"
end

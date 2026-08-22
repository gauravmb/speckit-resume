#!/usr/bin/env bash
set -e

# ==============================================================================
# speckit-resume: 1-Line Universal Installer & Project Configurator
# ==============================================================================

TARGET_DIR="${1:-.}"
cd "$TARGET_DIR"

echo "🚀 Installing speckit-resume for project in $(pwd)..."

# 1. Ensure .specify directory exists
if [ ! -d ".specify" ]; then
    echo "📦 Initializing .specify directory..."
    mkdir -p .specify/templates .specify/memory
fi

# 2. Add or update .specify/templates/tasks-template.md with the 5-state legend
cat << 'EOF' > .specify/templates/tasks-template.md
# Tasks: {{FEATURE_NAME}}

## Task State Legend
- [ ] Not started
- [~] In progress (see inline WIP checkpoint block)
- [?] Blocked on human decision/secret (see inline BLOCKED block)
- [-] Superseded / Deprecated (see inline PIVOT block)
- [X] Verified complete (passed gate.json quality gate)

---

## Phase 1: Setup & Foundations

- [ ] T001 [TYPE:CONFIG] Set up repository configuration and environment
- [ ] T002 [TYPE:TEST] Create foundational protocol definitions

EOF

# 3. Detect tech stack & create gate.json if missing
if [ ! -f "gate.json" ]; then
    echo "🔍 Auto-detecting project tech stack..."
    if [ -f "Package.swift" ] || ls *.xcodeproj 1> /dev/null 2>&1; then
        PROJECT_TYPE="swift-macos"
        TEST_CMD="xcodebuild test -scheme \$(xcodebuild -list -json | grep -o '\"name\":\"[^\"]*\"' | head -1 | cut -d'\"' -f4) -enableCodeCoverage YES"
        LINT_CMD="swiftlint lint"
    elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        PROJECT_TYPE="python"
        TEST_CMD="pytest"
        LINT_CMD="ruff check ."
    elif [ -f "package.json" ]; then
        PROJECT_TYPE="typescript-node"
        TEST_CMD="npm test"
        LINT_CMD="npm run lint"
    elif [ -f "Cargo.toml" ]; then
        PROJECT_TYPE="rust"
        TEST_CMD="cargo test"
        LINT_CMD="cargo clippy -- -D warnings"
    elif [ -f "go.mod" ]; then
        PROJECT_TYPE="go"
        TEST_CMD="go test ./..."
        LINT_CMD="golangci-lint run"
    else
        PROJECT_TYPE="generic"
        TEST_CMD="echo 'Configure test command in gate.json'"
        LINT_CMD="echo 'Configure lint command in gate.json'"
    fi

    cat << EOF > gate.json
{
  "version": "1.0",
  "project_type": "$PROJECT_TYPE",
  "commands": {
    "test": "$TEST_CMD",
    "lint": "$LINT_CMD"
  },
  "timeout_seconds": 180
}
EOF
    echo "✅ Created gate.json for $PROJECT_TYPE"
else
    echo "ℹ️ Existing gate.json found. Keeping current config."
fi

# 4. Create RESUME.md at project root
cat << 'EOF' > RESUME.md
# Resume Protocol (speckit-resume)

Whenever you open a new AI session or switch tools, paste this into chat:

> **Resume from feature.json and tasks.md. Follow .specify/memory/constitution.md.**

## Available Tools (MCP Server: speckit-resume)
- `get_active_task()`: Returns the active feature and in-progress micro-steps.
- `update_wip_step(task_id, sub_steps, completed_step_index, stopping_point)`: Records partial progress.
- `set_task_blocked(task_id, reason, action_required)`: Flags blockers requiring human action.
- `run_quality_gate(command_type)`: Runs tests & linters from gate.json.
- `complete_task(task_id)`: Verifies gate passes and marks task [X].
EOF
echo "✅ Created RESUME.md"

# 5. Create .cursor/mcp.json or print setup instructions
mkdir -p .cursor
cat << EOF > .cursor/mcp.json
{
  "mcpServers": {
    "speckit-resume": {
      "command": "$HOME/Documents/WorkingCopy/speckit-resume/.venv/bin/python",
      "args": ["$HOME/Documents/WorkingCopy/speckit-resume/src/server.py"]
    }
  }
}
EOF
echo "✅ Created .cursor/mcp.json"

echo ""
echo "🎉 speckit-resume installation complete!"
echo "👉 Simply open your AI tool and say: 'Resume from feature.json and tasks.md'"

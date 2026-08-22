# 🚀 speckit-resume

> **Universal, zero-loss MCP execution and resume engine for GitHub Spec-Kit.**

`speckit-resume` is a local Model Context Protocol (MCP) server that provides 100% truthful, interruption-proof state tracking, quality gate execution, and zero-loss resumption across AI coding assistants (**Antigravity, Cursor, Kiro, GitHub Copilot, Claude Code**).

---

## ✨ Key Features

- 🎯 **5-State Task Machine**: Deterministically tracks `[ ]` Pending, `[~]` In-Progress (WIP), `[?]` Blocked, `[-]` Superseded, and `[X]` Verified Complete.
- ⚡ **90%+ Token Compression**: Delivers only the active task and micro-steps to the AI (~60 tokens) instead of reading 500-line markdown files into context.
- 🛡️ **Quality Gate Guard**: Refuses to mark any task `[X]` unless local test suites and linters physically pass (`gate.json`).
- 📍 **Granular Sub-Step Checkpoints**: Saves exact line numbers and incomplete sub-steps when sessions drop or switch tools.
- 🔒 **100% Local & Private**: Runs on your local machine over standard `stdio`. Zero telemetry, zero external network calls.

---

## 📦 Quick Installation

In any project repository (existing or new), run:

```bash
curl -fsSL https://raw.githubusercontent.com/gauravmb/speckit-resume/main/install.sh | bash
```

This automatically:
1. Detects your programming language (Swift, Python, TypeScript, Rust, Go).
2. Generates `gate.json` and `RESUME.md`.
3. Upgrades `.specify/templates/tasks-template.md` with the 5-state resume engine.

---

## 🛠️ MCP Tools Exposed

| Tool Name | Purpose |
|---|---|
| `get_active_task(repo_path)` | Returns current active task ID, state, and micro-step checklist. |
| `update_wip_step(task_id, sub_steps, completed_step_index, stopping_point)` | Checkpoints in-progress sub-steps directly on disk. |
| `set_task_blocked(task_id, reason, action_required)` | Halts AI when an external secret or human decision is missing. |
| `run_quality_gate(command_type)` | Executes project test/lint commands from `gate.json`. |
| `complete_task(task_id)` | Runs gate, marks `[X]` in `tasks.md`, and clears WIP box. |

---

## ⚙️ MCP Client Configuration

Add to your MCP configuration file (`.cursor/mcp.json`, `~/.claude/mcp.json`, or Antigravity settings):

```json
{
  "mcpServers": {
    "speckit-resume": {
      "command": "python3",
      "args": ["/Users/gauravbhatia/Documents/WorkingCopy/speckit-resume/src/server.py"]
    }
  }
}
```

---

## 🧪 Running Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

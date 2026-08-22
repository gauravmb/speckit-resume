# 🚀 speckit-resume

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Spec-Kit](https://img.shields.io/badge/Spec--Kit-Companion-orange.svg)](https://github.com/github/spec-kit)
[![Zero Install](https://img.shields.io/badge/Setup-Zero--Install%20(uvx)-brightgreen.svg)](#-zero-install-setup)

> **The Universal, Zero-Loss Execution & Resumption Engine for GitHub Spec-Kit.**  
> *Interruption-proof state tracking, quality gate enforcement, and 90%+ token compression for AI coding assistants.*

---

## ⚡ Zero-Install Setup (No Python/Pip Management Required)

`speckit-resume` runs **ephemerally in memory directly from GitHub using `uvx`**.  
You do **NOT** need to create virtual environments, install Python packages, or manage dependencies on your machine.

---

## 🔌 Connect to Your AI Tools (1-Step Configuration)

### 1. Google Antigravity (`agy`)
Run this single command in your terminal:
```bash
agy mcp add speckit-resume uvx -- --from git+https://github.com/gauravmb/speckit-resume.git speckit-resume
```

### 2. Cursor & Kiro
Add to `.cursor/mcp.json` or `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "speckit-resume": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/gauravmb/speckit-resume.git", "speckit-resume"]
    }
  }
}
```

### 3. VS Code & GitHub Copilot
Add to `.vscode/mcp.json`:
```json
{
  "mcpServers": {
    "speckit-resume": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/gauravmb/speckit-resume.git", "speckit-resume"]
    }
  }
}
```

### 4. Claude Desktop & Claude Code
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows):
```json
{
  "mcpServers": {
    "speckit-resume": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/gauravmb/speckit-resume.git", "speckit-resume"]
    }
  }
}
```

---

## 💡 Why speckit-resume?

[GitHub Spec-Kit](https://github.com/github/spec-kit) is extraordinary at **planning** software (`specify` ➔ `plan` ➔ `tasks`). However, during the **implementation** phase, real-world AI coding hits major roadblocks:

1. 💸 **Token Explosion**: When an AI reads 500-line `tasks.md` and `plan.md` files over and over, it wastes 10,000+ tokens on every turn.
2. 🔄 **Context Loss on Session Drops**: When token quotas expire, accounts switch, or you move from Copilot to Cursor or Antigravity, the incoming AI has no memory of which sub-step or line was being written.
3. 🤥 **Fake Checkbox Hallucinations**: Standard LLMs often claim: *"I have completed all tasks for you!"* and tick `[X]` without actually running tests or writing working code.
4. 💥 **Overwriting & Duplicate Code**: Unaware of what is half-written, incoming agents restart tasks from scratch and overwrite existing progress.

**`speckit-resume` solves all 4 problems permanently.**

---

## 🤝 How it Works with Spec-Kit

`speckit-resume` is the **runtime execution companion** to GitHub Spec-Kit:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. SPEC-KIT OWNS: The Planning Pipeline                                │
│    /speckit-specify   ──► Generates spec.md                            │
│    /speckit-plan      ──► Generates plan.md, research.md, data-model.md │
│    /speckit-tasks     ──► Generates tasks.md                           │
├────────────────────────────────────────────────────────────────────────┤
│ 2. SPECKIT-RESUME OWNS: The Execution & Resume Engine                  │
│    /speckit-implement ──► Executes tasks with 5-state tracking         │
│    Session Ends / Cut ──► Writes Granular WIP Checkpoint block         │
│    Resume in ANY Tool ──► Reads feature.json + tasks.md + git diff     │
│    Quality Gate Guard ──► Executes gate.json (Tests + Linters)         │
└────────────────────────────────────────────────────────────────────────┘
```

You keep using standard Spec-Kit commands for planning. `speckit-resume` takes over during implementation to guarantee you can stop, switch tools, or log out at any millisecond and resume with 100% precision.

---

## ⚡ Core Capabilities

- 🎯 **5-State Deterministic Task Engine**: Replaces binary `[ ]`/`[X]` with a complete state machine (`Pending`, `In-Progress`, `Blocked`, `Superseded`, `Verified Complete`).
- ⚡ **90%+ Token Compression**: Delivers only the active task and micro-steps to the AI context (~60 tokens) instead of dumping 500 lines of markdown.
- 🛡️ **Quality Gate Guard (The Referee)**: Refuses to mark any task `[X]` unless local test suites and linters physically pass (`gate.json`).
- 📍 **Granular Sub-Step Checkpoints**: Saves exact line numbers, incomplete sub-steps, and file paths when sessions drop.
- 🔒 **100% Local & Private**: Runs on your local machine over standard `stdio`. Zero telemetry, zero external network calls.

---

## 📊 The 5-State Task Machine

`speckit-resume` manages tasks across 5 distinct states:

| State | Name | Meaning | What the AI Does |
|---|---|---|---|
| `- [ ]` | **Pending** | Not started. | Checks dependencies ➔ writes failing test (TDD) ➔ begins. |
| `- [~]` | **In-Progress** | Active WIP checkpoint exists. | Inspects diff ➔ runs tests ➔ continues exact sub-step. |
| `- [?]` | **Blocked** | Blocked on human decision or secret. | **HALTS**. Notifies human and waits for unblock. |
| `- [-]` | **Superseded** | Architecturally deprecated / pivoted. | Skips and executes replacement sub-tasks. |
| `- [X]` | **Verified** | Passed project quality gate. | Complete. Verified by local compiler/test suite. |

### Example In-Progress Checkpoint (`[~]`):
```markdown
- [~] T026 [TYPE:TEST] Implement StandardDDCController
      ┌── WIP CHECKPOINT ────────────────────────────────────────────────────────┐
      │ Updated: 2026-08-22T10:30:00Z | Tool: Cursor                            │
      │ Sub-steps:                                                               │
      │   [x] 1. Register CGDisplayRegisterReconfigurationCallback               │
      │   [x] 2. Set up IOKit display matching                                   │
      │   [ ] 3. Implement EDID raw byte reader                                  │
      │   [ ] 4. Parse vendor ID, product ID, serial number                      │
      │ Stopping Point: Line 48 in StandardDDCController.swift (readEDID stub)   │
      └──────────────────────────────────────────────────────────────────────────┘
```

---

## 🏃 Day-to-Day Workflow

### Step 1: Plan with Spec-Kit
Run your normal Spec-Kit commands in your AI chat:
```text
/speckit-specify "Build external monitor brightness control"
/speckit-plan
/speckit-tasks
```

### Step 2: Start or Resume Coding in ANY Tool
Whenever you open a new session or switch AI tools, simply paste:
> **`Resume from feature.json and tasks.md. Follow .specify/memory/constitution.md.`**

### Step 3: What the AI Automatically Does
```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant AI as AI Model (Copilot/Cursor/Antigravity)
    participant MCP as speckit-resume MCP Server (uvx)
    participant Repo as Local Repo (tasks.md, gate.json)

    Dev->>AI: "Resume"
    AI->>MCP: get_active_task()
    MCP->>Repo: Reads feature.json, tasks.md
    MCP-->>AI: Returns active task JSON (60 tokens)
    
    AI->>AI: Writes tests (TDD) and code for active sub-step
    
    AI->>MCP: run_quality_gate()
    MCP->>Repo: Executes local test suite from gate.json
    MCP-->>AI: {"passed": true, "output": "Tests passed: 28"}
    
    AI->>MCP: complete_task("T018")
    MCP->>Repo: Marks [X] in tasks.md
    MCP-->>AI: {"success": true, "next_task": "T019"}
    AI-->>Dev: "Task T018 verified and complete. Starting T019."
```

---

## ⚙️ Configuration Reference (`gate.json`)

`gate.json` at your project root defines how quality gates are executed on your machine:

```json
{
  "version": "1.0",
  "project_type": "swift-macos",
  "commands": {
    "test": "xcodebuild test -project ExternalDisplayController.xcodeproj -scheme ExternalDisplayController -destination 'platform=macOS' -enableCodeCoverage YES",
    "lint": "swiftlint lint --config .swiftlint.yml",
    "build": "xcodebuild build -project ExternalDisplayController.xcodeproj -scheme ExternalDisplayController"
  },
  "timeout_seconds": 180,
  "coverage_threshold_percent": 80
}
```

*Works identically for Python (`pytest`), Rust (`cargo test`), Node (`npm test`), and Go (`go test`).*

---

## 📄 License
MIT © 2026 Gaurav Bhatia

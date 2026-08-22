import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TaskEngine:
    """
    Parses and updates `tasks.md` deterministically across the 5 standard states:
      [ ] Pending
      [~] In Progress (WIP)
      [?] Blocked
      [-] Superseded (Pivot)
      [X] Verified Complete
    """

    TASK_PATTERN = re.compile(r"^-\s*\[([ ~?\-X])\]\s*(T\d+)\s*(.*)")
    WIP_BOX_START = "┌── WIP CHECKPOINT"
    WIP_BOX_END = "└──────────────────────────────────────────────────────────────────────────┘"

    def get_feature_context(self, repo_path: str) -> Dict[str, Any]:
        """Resolves the active feature directory from .specify/feature.json."""
        feature_json = os.path.join(repo_path, ".specify", "feature.json")
        if not os.path.exists(feature_json):
            return {
                "error": "Missing .specify/feature.json. Ensure Spec-Kit is initialized."
            }

        try:
            with open(feature_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            feature_dir = data.get("feature_directory")
            if not feature_dir:
                return {"error": ".specify/feature.json missing 'feature_directory' key."}

            tasks_path = os.path.join(repo_path, feature_dir, "tasks.md")
            return {
                "feature_directory": feature_dir,
                "tasks_path": tasks_path,
                "exists": os.path.exists(tasks_path)
            }
        except Exception as e:
            return {"error": f"Failed to read feature.json: {str(e)}"}

    def get_active_task(self, repo_path: str) -> Dict[str, Any]:
        """
        Scans tasks.md for the active feature:
          1. First checks for [?] Blocked task (stops if found).
          2. Next checks for [~] In-Progress task.
          3. Next checks for [ ] Pending task.
          4. Returns state, task ID, title, and sub-steps without reading entire file into LLM context.
        """
        ctx = self.get_feature_context(repo_path)
        if "error" in ctx:
            return ctx
        if not ctx["exists"]:
            return {
                "state": "NO_TASKS_FILE",
                "message": f"tasks.md not found at {ctx['tasks_path']}. Run Spec-Kit tasks command first.",
                "feature_directory": ctx["feature_directory"]
            }

        with open(ctx["tasks_path"], "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Pass 1: Find [?] Blocked
        for i, line in enumerate(lines):
            match = self.TASK_PATTERN.match(line)
            if match and match.group(1) == "?":
                task_id = match.group(2)
                title = match.group(3).strip()
                block_details = self._extract_block(lines, i)
                return {
                    "state": "BLOCKED",
                    "task_id": task_id,
                    "title": title,
                    "details": block_details,
                    "feature_directory": ctx["feature_directory"],
                    "action_required": "Task is blocked on human decision/secret. Resolve blocker before continuing."
                }

        # Pass 2: Find [~] In-Progress (WIP)
        for i, line in enumerate(lines):
            match = self.TASK_PATTERN.match(line)
            if match and match.group(1) == "~":
                task_id = match.group(2)
                title = match.group(3).strip()
                block_details = self._extract_block(lines, i)
                return {
                    "state": "IN_PROGRESS",
                    "task_id": task_id,
                    "title": title,
                    "wip_checkpoint": block_details,
                    "feature_directory": ctx["feature_directory"],
                    "action_required": "Continue from current stopping point in WIP checkpoint."
                }

        # Pass 3: Find first [ ] Pending
        for i, line in enumerate(lines):
            match = self.TASK_PATTERN.match(line)
            if match and match.group(1) == " ":
                task_id = match.group(2)
                title = match.group(3).strip()
                return {
                    "state": "PENDING",
                    "task_id": task_id,
                    "title": title,
                    "feature_directory": ctx["feature_directory"],
                    "action_required": f"Start task {task_id}: write failing test first (TDD), implement, and verify gate."
                }

        return {
            "state": "ALL_COMPLETED",
            "message": "All tasks in this feature are marked [X] Verified Complete.",
            "feature_directory": ctx["feature_directory"]
        }

    def update_wip(
        self,
        repo_path: str,
        task_id: str,
        sub_steps: List[str],
        completed_step_index: int,
        stopping_point: str,
        tool_name: str = "speckit-resume"
    ) -> Dict[str, Any]:
        """
        Updates task to [~] and writes a structured WIP checkpoint directly under it.
        """
        ctx = self.get_feature_context(repo_path)
        if "error" in ctx or not ctx["exists"]:
            return {"success": False, "error": ctx.get("error", "tasks.md not found")}

        with open(ctx["tasks_path"], "r", encoding="utf-8") as f:
            content = f.read()

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build clean WIP checkpoint text
        sub_step_lines = []
        for idx, step_desc in enumerate(sub_steps):
            box = "[x]" if idx <= completed_step_index else "[ ]"
            sub_step_lines.append(f"      │   {box} {idx + 1}. {step_desc}")

        wip_box = (
            f"      ┌── WIP CHECKPOINT ────────────────────────────────────────┐\n"
            f"      │ Updated: {now_utc} | Tool: {tool_name}\n"
            f"      │ Sub-steps:\n"
            + "\n".join(sub_step_lines) + "\n"
            f"      │ Stopping Point: {stopping_point}\n"
            f"      └──────────────────────────────────────────────────────────┘\n"
        )

        lines = content.splitlines(keepends=True)
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            match = self.TASK_PATTERN.match(line)
            if match and match.group(2) == task_id:
                # Replace state with [~]
                new_title_line = re.sub(r"^-\s*\[[ ~?\-X]\]", "- [~]", line)
                new_lines.append(new_title_line)

                # Skip any existing WIP/BLOCKED box under this task
                i += 1
                while i < len(lines) and (lines[i].startswith("      ┌──") or lines[i].startswith("      │") or lines[i].startswith("      └──")):
                    i += 1

                new_lines.append(wip_box)
                continue
            else:
                new_lines.append(line)
                i += 1

        with open(ctx["tasks_path"], "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return {"success": True, "task_id": task_id, "state": "IN_PROGRESS", "timestamp": now_utc}

    def set_blocked(
        self,
        repo_path: str,
        task_id: str,
        reason: str,
        action_required: str,
        tool_name: str = "speckit-resume"
    ) -> Dict[str, Any]:
        """Marks a task [?] and records a structured BLOCKED box."""
        ctx = self.get_feature_context(repo_path)
        if "error" in ctx or not ctx["exists"]:
            return {"success": False, "error": ctx.get("error", "tasks.md not found")}

        with open(ctx["tasks_path"], "r", encoding="utf-8") as f:
            lines = f.readlines()

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        blocked_box = (
            f"      ┌── BLOCKED: HUMAN ACTION REQUIRED ────────────────────────┐\n"
            f"      │ Blocked At: {now_utc} | Tool: {tool_name}\n"
            f"      │ Reason: {reason}\n"
            f"      │ Action Required: {action_required}\n"
            f"      └──────────────────────────────────────────────────────────┘\n"
        )

        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            match = self.TASK_PATTERN.match(line)
            if match and match.group(2) == task_id:
                new_title_line = re.sub(r"^-\s*\[[ ~?\-X]\]", "- [?]", line)
                new_lines.append(new_title_line)

                i += 1
                while i < len(lines) and (lines[i].startswith("      ┌──") or lines[i].startswith("      │") or lines[i].startswith("      └──")):
                    i += 1

                new_lines.append(blocked_box)
                continue
            else:
                new_lines.append(line)
                i += 1

        with open(ctx["tasks_path"], "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return {"success": True, "task_id": task_id, "state": "BLOCKED"}

    def mark_done(self, repo_path: str, task_id: str) -> Dict[str, Any]:
        """
        Marks task as [X] Verified Complete and removes any WIP/BLOCKED box.
        """
        ctx = self.get_feature_context(repo_path)
        if "error" in ctx or not ctx["exists"]:
            return {"success": False, "error": ctx.get("error", "tasks.md not found")}

        with open(ctx["tasks_path"], "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        i = 0
        found = False
        while i < len(lines):
            line = lines[i]
            match = self.TASK_PATTERN.match(line)
            if match and match.group(2) == task_id:
                found = True
                new_title_line = re.sub(r"^-\s*\[[ ~?\-X]\]", "- [X]", line)
                new_lines.append(new_title_line)

                # Skip any WIP/BLOCKED box attached to this task
                i += 1
                while i < len(lines) and (lines[i].startswith("      ┌──") or lines[i].startswith("      │") or lines[i].startswith("      └──")):
                    i += 1
                continue
            else:
                new_lines.append(line)
                i += 1

        if not found:
            return {"success": False, "error": f"Task ID {task_id} not found in tasks.md"}

        with open(ctx["tasks_path"], "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return {"success": True, "task_id": task_id, "state": "VERIFIED"}

    def _extract_block(self, lines: List[str], start_index: int) -> str:
        """Helper to extract formatted WIP or BLOCKED box directly below a task line."""
        block_lines = []
        for j in range(start_index + 1, min(start_index + 20, len(lines))):
            line = lines[j]
            if line.startswith("      ┌──") or line.startswith("      │") or line.startswith("      └──"):
                block_lines.append(line.strip())
            else:
                break
        return "\n".join(block_lines)

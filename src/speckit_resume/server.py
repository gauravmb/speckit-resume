import asyncio
import os
import sys
from typing import Any, Dict, List, Optional

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(__file__))

from gate_runner import GateRunner
from mcp.server import MCPServer
from task_engine import TaskEngine

# Initialize MCPServer
server = MCPServer("speckit-resume")
engine = TaskEngine()
runner = GateRunner()


@server.tool()
def get_active_task(repo_path: str = ".") -> Dict[str, Any]:
    """
    Returns the active feature, active task ID, state, and WIP sub-steps.
    Use this immediately when resuming or starting work on a feature.
    """
    return engine.get_active_task(repo_path)


@server.tool()
def update_wip_step(
    task_id: str,
    sub_steps: List[str],
    completed_step_index: int,
    stopping_point: str,
    repo_path: str = "."
) -> Dict[str, Any]:
    """
    Records granular in-progress work and sub-step completion for a task.
    Call this whenever a sub-step is finished or before ending a session turn.
    """
    return engine.update_wip(
        repo_path=repo_path,
        task_id=task_id,
        sub_steps=sub_steps,
        completed_step_index=completed_step_index,
        stopping_point=stopping_point
    )


@server.tool()
def set_task_blocked(
    task_id: str,
    reason: str,
    action_required: str,
    repo_path: str = "."
) -> Dict[str, Any]:
    """
    Marks a task as [?] Blocked when human input, API secret, or decision is required.
    Stops the AI from guessing or making up invalid code.
    """
    return engine.set_blocked(
        repo_path=repo_path,
        task_id=task_id,
        reason=reason,
        action_required=action_required
    )


@server.tool()
def run_quality_gate(command_type: str = "test", repo_path: str = ".") -> Dict[str, Any]:
    """
    Executes project quality gates (test, lint, build) configured in gate.json.
    Returns token-compressed pass/fail diagnostic output.
    """
    return runner.run_command(repo_path=repo_path, command_type=command_type)


@server.tool()
def complete_task(task_id: str, skip_gate_check: bool = False, repo_path: str = ".") -> Dict[str, Any]:
    """
    Verifies that the project quality gate passes, marks the task [X] Verified Complete,
    and removes any WIP checkpoint block.
    """
    if not skip_gate_check:
        gate_res = runner.run_command(repo_path=repo_path, command_type="test")
        if not gate_res["passed"]:
            return {
                "success": False,
                "error": "Cannot complete task: Quality gate failed (tests/linters failing). Fix errors first.",
                "gate_output": gate_res.get("output", "")
            }

    return engine.mark_done(repo_path=repo_path, task_id=task_id)


def main():
    """Entrypoint for running the speckit-resume MCP server over stdio."""
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()

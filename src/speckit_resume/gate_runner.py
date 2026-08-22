import json
import os
import subprocess
from typing import Any, Dict


class GateRunner:
    """
    Executes project-specific quality gates (tests, linter, typecheck, build)
    configured in the target project's `gate.json`.
    """

    def run_command(self, repo_path: str, command_type: str = "test") -> Dict[str, Any]:
        """
        Runs a command from gate.json within the target repo directory.
        Returns a structured dictionary with pass/fail and token-compressed logs.
        """
        gate_file = os.path.join(repo_path, "gate.json")
        if not os.path.exists(gate_file):
            return {
                "passed": False,
                "exit_code": -1,
                "error": f"Missing gate.json at {gate_file}. Run 'speckit-resume init' or create gate.json.",
                "output": ""
            }

        try:
            with open(gate_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            return {
                "passed": False,
                "exit_code": -1,
                "error": f"Failed to parse gate.json: {str(e)}",
                "output": ""
            }

        commands = config.get("commands", {})
        cmd = commands.get(command_type)

        if not cmd:
            return {
                "passed": False,
                "exit_code": -1,
                "error": f"Command type '{command_type}' not defined in gate.json. Available: {list(commands.keys())}",
                "output": ""
            }

        # Execute command in repo working directory
        try:
            process = subprocess.run(
                cmd,
                shell=True,
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=config.get("timeout_seconds", 180)
            )
            raw_output = process.stdout or ""
            passed = (process.returncode == 0)

            # Token compression: keep only the most relevant diagnostic lines (last 2000 chars)
            compressed_output = raw_output[-2000:] if len(raw_output) > 2000 else raw_output

            return {
                "passed": passed,
                "exit_code": process.returncode,
                "command_executed": cmd,
                "output": compressed_output,
                "error": None if passed else "Quality gate command failed (non-zero exit code)."
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "exit_code": -1,
                "error": f"Command timed out after {config.get('timeout_seconds', 180)} seconds.",
                "output": ""
            }
        except Exception as e:
            return {
                "passed": False,
                "exit_code": -1,
                "error": f"Execution error: {str(e)}",
                "output": ""
            }

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from task_engine import TaskEngine
from gate_runner import GateRunner


class TestTaskEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.specify_dir = os.path.join(self.temp_dir, ".specify")
        os.makedirs(self.specify_dir)

        self.feature_dir = os.path.join(self.temp_dir, "specs", "001-test-feature")
        os.makedirs(self.feature_dir)

        # Write .specify/feature.json
        feature_json_path = os.path.join(self.specify_dir, "feature.json")
        with open(feature_json_path, "w", encoding="utf-8") as f:
            json.dump({"feature_directory": "specs/001-test-feature"}, f)

        # Write sample tasks.md
        self.tasks_path = os.path.join(self.feature_dir, "tasks.md")
        self.sample_tasks = (
            "# Feature Tasks\n\n"
            "- [X] T001 [TYPE:CONFIG] Setup initial project\n"
            "- [ ] T002 [TYPE:TEST] Implement Parser logic\n"
            "- [ ] T003 [TYPE:TEST] Add integration test\n"
        )
        with open(self.tasks_path, "w", encoding="utf-8") as f:
            f.write(self.sample_tasks)

        self.engine = TaskEngine()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_finds_first_pending_task(self):
        active = self.engine.get_active_task(self.temp_dir)
        self.assertEqual(active["state"], "PENDING")
        self.assertEqual(active["task_id"], "T002")

    def test_updates_wip_step_and_persists_box(self):
        sub_steps = [
            "Define protocol interface",
            "Implement lexer tokenizer",
            "Write AST parser"
        ]
        res = self.engine.update_wip(
            repo_path=self.temp_dir,
            task_id="T002",
            sub_steps=sub_steps,
            completed_step_index=1,
            stopping_point="Line 54 in Parser.swift (AST parser stub)"
        )
        self.assertTrue(res["success"])

        # Re-query active task
        active = self.engine.get_active_task(self.temp_dir)
        self.assertEqual(active["state"], "IN_PROGRESS")
        self.assertEqual(active["task_id"], "T002")
        self.assertIn("WIP CHECKPOINT", active["wip_checkpoint"])
        self.assertIn("[x] 2. Implement lexer tokenizer", active["wip_checkpoint"])
        self.assertIn("[ ] 3. Write AST parser", active["wip_checkpoint"])

    def test_sets_blocked_task_and_halts_flow(self):
        res = self.engine.set_blocked(
            repo_path=self.temp_dir,
            task_id="T002",
            reason="Missing API secret KEY_XYZ",
            action_required="Add KEY_XYZ to .env"
        )
        self.assertTrue(res["success"])

        active = self.engine.get_active_task(self.temp_dir)
        self.assertEqual(active["state"], "BLOCKED")
        self.assertEqual(active["task_id"], "T002")
        self.assertIn("BLOCKED: HUMAN ACTION REQUIRED", active["details"])
        self.assertIn("Missing API secret KEY_XYZ", active["details"])

    def test_marks_done_and_cleans_box(self):
        # First set WIP
        self.engine.update_wip(
            repo_path=self.temp_dir,
            task_id="T002",
            sub_steps=["Step 1", "Step 2"],
            completed_step_index=1,
            stopping_point="Done"
        )

        # Mark done
        res = self.engine.mark_done(self.temp_dir, "T002")
        self.assertTrue(res["success"])

        # Now active task should automatically advance to T003!
        active = self.engine.get_active_task(self.temp_dir)
        self.assertEqual(active["state"], "PENDING")
        self.assertEqual(active["task_id"], "T003")


class TestGateRunner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.gate_file = os.path.join(self.temp_dir, "gate.json")
        with open(self.gate_file, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.0",
                "commands": {
                    "test": "echo 'TEST_PASSED'",
                    "fail_test": "exit 1"
                }
            }, f)
        self.runner = GateRunner()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_runs_successful_command(self):
        res = self.runner.run_command(self.temp_dir, "test")
        self.assertTrue(res["passed"])
        self.assertIn("TEST_PASSED", res["output"])

    def test_detects_failed_command(self):
        res = self.runner.run_command(self.temp_dir, "fail_test")
        self.assertFalse(res["passed"])
        self.assertEqual(res["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()

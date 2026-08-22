import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from speckit_resume.server import server


class TestMCPProtocol(unittest.IsolatedAsyncioTestCase):
    async def test_tools_listed(self):
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]
        print("\n✅ Verified MCP Registered Tools:", tool_names)

        self.assertIn("get_active_task", tool_names)
        self.assertIn("update_wip_step", tool_names)
        self.assertIn("set_task_blocked", tool_names)
        self.assertIn("run_quality_gate", tool_names)
        self.assertIn("complete_task", tool_names)

    async def test_get_active_task_tool_call(self):
        repo_path = "/Users/gauravbhatia/Documents/WorkingCopy/ExternalDisplayController"
        result = await server.call_tool("get_active_task", {"repo_path": repo_path})
        print("✅ MCP Tool Call (get_active_task) Output:", result.structured_content)

        self.assertFalse(result.is_error)
        data = result.structured_content.get("result", result.structured_content)
        self.assertEqual(data.get("task_id"), "T018")
        self.assertEqual(data.get("state"), "PENDING")

    async def test_run_quality_gate_tool_call(self):
        repo_path = "/Users/gauravbhatia/Documents/WorkingCopy/ExternalDisplayController"
        result = await server.call_tool("run_quality_gate", {"command_type": "lint", "repo_path": repo_path})
        print("✅ MCP Tool Call (run_quality_gate) Output:", result.structured_content)

        self.assertFalse(result.is_error)
        data = result.structured_content.get("result", result.structured_content)
        self.assertTrue(data.get("passed"))


if __name__ == "__main__":
    unittest.main()

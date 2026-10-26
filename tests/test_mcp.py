import asyncio
import json
import subprocess
import sys
import unittest
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


ROOT = Path(__file__).resolve().parents[1]


def cli_result(arguments):
    args = [item for key, value in arguments.items() for item in (f"--{key}", str(value))]
    completed = subprocess.run([sys.executable, "-m", "cli.main", *args], cwd=ROOT, capture_output=True, text=True)
    return completed.returncode, completed.stdout.strip()


class MCPProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_tools_list_and_all_public_vectors(self):
        params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"], cwd=ROOT)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed = await session.list_tools()
                self.assertEqual([tool.name for tool in listed.tools], ["power_analysis"])

                rows = [json.loads(line) for line in (ROOT / "public_vectors.jsonl").read_text().splitlines() if line]
                for row in rows:
                    expected_code, expected_text = cli_result(row["input"])
                    result = await session.call_tool("power_analysis", row["input"])
                    self.assertEqual(len(result.content), 1, row["id"])
                    self.assertEqual(result.content[0].type, "text", row["id"])
                    self.assertEqual(result.content[0].text, expected_text, row["id"])
                    self.assertEqual(bool(result.is_error), expected_code != 0, row["id"])

                # REA-015: exercise the same boundary through the sole MCP
                # tool and require byte-for-byte CLI/MCP equivalence.
                for mode in ("a-priori", "post-hoc", "compromise", "criterion"):
                    for d in (20, 20.0001, 21, 100, 1000):
                        if d == 20 and mode != "a-priori":
                            continue
                        values = {"test": "t2-indep", "mode": mode, "tails": 1, "d": d}
                        if mode == "a-priori":
                            values.update(alpha=.05, power=.8, ratio=1)
                        elif mode == "post-hoc":
                            values.update(alpha=.05, n1=2, n2=2)
                        elif mode == "compromise":
                            values.update(beta_alpha_ratio=1, n1=2, n2=2)
                        else:
                            values.update(power=.8, n1=2, n2=2)
                        expected_code, expected_text = cli_result(values)
                        result = await session.call_tool("power_analysis", values)
                        self.assertEqual(result.content[0].text, expected_text, ("REA-015", mode, d))
                        self.assertEqual(bool(result.is_error), expected_code != 0, ("REA-015", mode, d))


if __name__ == "__main__":
    unittest.main()

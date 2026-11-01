"""
Standard Model Context Protocol (MCP) Server for Tandem Mesh.

Exposes Tandem mesh capabilities over standard JSON-RPC 2.0 stdio, allowing
instant integration into Claude Desktop, Cursor, Antigravity IDE, or any MCP-compliant harness.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

from tandem.core.router import IntentRouter
from tandem.harness.adapter import HarnessMeshAdapter


class TandemMcpServer:
    """
    Standard MCP Stdio protocol handler for Tandem.
    """

    def __init__(self, router: IntentRouter) -> None:
        self.router = router
        self.adapter = HarnessMeshAdapter(router=router, agent_id="mcp_harness")

    def run_stdio(self) -> None:
        """Run loop reading newline-delimited JSON-RPC from stdin."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                response = self.handle_message(msg)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": None,
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

    def handle_message(self, msg: dict[str, Any]) -> Optional[dict[str, Any]]:
        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "tandem-mesh-mcp",
                        "version": "0.1.0",
                    },
                },
            }

        elif method == "tools/list":
            raw_tools = self.adapter.get_tool_definitions()
            mcp_tools = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["parameters"],
                }
                for t in raw_tools
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": mcp_tools}}

        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})
            res = self.adapter.execute_tool(tool_name, args)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, indent=2)}]
                },
            }

        elif method == "notifications/initialized":
            return None

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }


def main() -> None:
    router = IntentRouter()
    server = TandemMcpServer(router=router)
    server.run_stdio()


if __name__ == "__main__":
    main()

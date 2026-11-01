"""
Universal Agent Harness Adapter.

Exposes Tandem mesh capabilities and A2H physical agency to any AI agent harness:
  - Antigravity / Gemini CLI
  - Harness² (8 editable components: prompt, tools, memory, subagents, etc.)
  - Claude Code / OpenCode / Codex / Cursor
  - Model Context Protocol (MCP) clients
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from tandem.core.router import IntentRouter
from tandem.core.types import (
    AutonomyGear,
    BlastRadiusRatificationRequired,
    HandDevice,
    IntentRequest,
    IntentResponse,
    TaintLevel,
)


class HarnessMeshAdapter:
    """
    High-ergonomics adapter connecting an LLM agent harness to the Tandem mesh.
    """

    def __init__(
        self,
        router: IntentRouter,
        agent_id: str = "antigravity_agent",
        default_taint: TaintLevel = TaintLevel.INTERNAL_AGENT,
    ) -> None:
        self.router = router
        self.agent_id = agent_id
        self.default_taint = default_taint

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """
        Exports all registered mesh capabilities as standardized JSON-Schema tool definitions.
        Universally compatible with Gemini function calling, OpenAI tools, Anthropic, and MCP.
        """
        tools: list[dict[str, Any]] = []

        # Mesh metadata and discovery tool
        tools.append(
            {
                "name": "tandem_discover_capabilities",
                "description": "Discover all applications and capabilities currently connected to the Tandem mesh.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prefix": {
                            "type": "string",
                            "description": "Optional prefix to filter capabilities by domain (e.g. 'cad.', 'sim.', 'voice.').",
                        }
                    },
                    "required": [],
                },
            }
        )

        # Mesh e-brake status & emergency stop
        tools.append(
            {
                "name": "tandem_emergency_halt",
                "description": "Immediately trigger the physical emergency E-Brake across all mesh apps and devices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string", "description": "Reason for triggering E-Brake."}
                    },
                    "required": ["reason"],
                },
            }
        )

        # Mesh e-brake release & restore operation
        tools.append(
            {
                "name": "tandem_release_halt",
                "description": "Release the emergency E-Brake across all mesh apps and devices, restoring standard operation.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            }
        )

        # Export each registered capability as a callable tool
        for cap in self.router.registry.list_capabilities():
            param_props: dict[str, Any] = {}
            required_params: list[str] = []

            for p in cap.parameters:
                json_type = p.type_name
                if json_type in ("int", "float"):
                    json_type = "number"
                elif json_type in ("dict", "any"):
                    json_type = "object"
                elif json_type == "list":
                    json_type = "array"

                param_props[p.name] = {
                    "type": json_type,
                    "description": p.description,
                }
                if p.required:
                    required_params.append(p.name)

            tool_name = f"mesh_{cap.name.replace('.', '_')}"
            desc = (
                f"{cap.description} (Blast Radius: {cap.blast_radius}/100, "
                f"Min Taint: {cap.min_taint_level.name})"
            )

            tools.append(
                {
                    "name": tool_name,
                    "description": desc,
                    "parameters": {
                        "type": "object",
                        "properties": param_props,
                        "required": required_params,
                    },
                }
            )

        return tools

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a harness tool call against the Tandem mesh.
        """
        if tool_name == "tandem_discover_capabilities":
            prefix = arguments.get("prefix")
            caps = self.router.registry.list_capabilities(prefix=prefix)
            return {
                "success": True,
                "capabilities": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "blast_radius": c.blast_radius,
                        "min_taint_level": c.min_taint_level.name,
                        "parameters": [p.name for p in c.parameters],
                    }
                    for c in caps
                ],
            }

        if tool_name == "tandem_emergency_halt":
            reason = arguments.get("reason", "Harness emergency stop")
            self.router.press_ebrake(source=f"agent:{self.agent_id}")
            return {
                "success": True,
                "message": f"Mesh E-Brake engaged: {reason}",
                "active_gear": "G0_EBRAKE_STOP",
            }

        if tool_name == "tandem_release_halt":
            self.router.release_ebrake()
            return {
                "success": True,
                "message": "Mesh E-Brake released. Restored to G2_SPORT_TACTILE.",
                "active_gear": "G2_SPORT_TACTILE",
            }

        # Resolve capability from tool name (mesh_domain_method -> domain.method)
        if tool_name.startswith("mesh_"):
            raw_cap_name = tool_name[5:]
            # Match against registered capabilities
            target_cap: Optional[str] = None
            for c in self.router.registry.list_capabilities():
                if c.name.replace(".", "_") == raw_cap_name:
                    target_cap = c.name
                    break

            if not target_cap:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' does not map to any known capability.",
                }

            import uuid

            req = IntentRequest(
                request_id=f"req_{uuid.uuid4().hex[:8]}",
                target_capability=target_cap,
                params=arguments,
                caller_app_id=self.agent_id,
                caller_taint=self.default_taint,
            )

            try:
                resp = self.router.dispatch(req)
                out: dict[str, Any] = {
                    "success": resp.success,
                    "data": resp.data,
                    "execution_time_ms": resp.execution_time_ms,
                }
                if resp.error:
                    out["error"] = resp.error
                if resp.haptic_telemetry:
                    out["haptic_profile"] = resp.haptic_telemetry.to_dict()
                return out
            except Exception as e:
                err_dict: dict[str, Any] = {
                    "success": False,
                    "error": f"{type(e).__name__}: {str(e)}",
                }
                if isinstance(e, BlastRadiusRatificationRequired) and e.haptic_profile is not None:
                    err_dict["haptic_profile"] = e.haptic_profile.to_dict()
                return err_dict

        return {"success": False, "error": f"Unknown harness tool: {tool_name}"}

    def render_system_prompt_snippet(self) -> str:
        """
        Generates prompt instructions for the agent harness to know how to use the mesh.
        """
        caps = self.router.registry.list_capabilities()
        primary_hand = self.router.get_primary_hand()
        gear_name = primary_hand.active_gear.name if primary_hand else "G2_SPORT_TACTILE"

        lines = [
            "### 🌐 Tandem Universal Coordination Mesh (A2A & A2H)",
            f"- Active Agent: `{self.agent_id}`",
            f"- Connected Hand Controller: `{primary_hand.device_type if primary_hand else 'Virtual'}` (Autonomy Gear: `{gear_name}`)",
            "- Available Capabilities:",
        ]
        for c in caps:
            lines.append(f"  * `{c.name}`: {c.description} [Blast Radius: {c.blast_radius}]")
        lines.append(
            "- Invariant: High blast-radius operations trigger physical tactile detents on the operator's hand before execution."
        )
        return "\n".join(lines)

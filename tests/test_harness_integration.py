"""
Unit tests for Universal Agent Harness Integration and Deep Module leverage.
"""

from __future__ import annotations

import unittest

from tandem.client import Tandem
from tandem.core.types import (
    AutonomyGear,
    CapabilityParameter,
    TaintLevel,
)


class TestHarnessIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.node = Tandem.local(app_id="flight_sim_harness")

        # Register a simulation capability
        self.node.register_capability(
            name="sim.apply_thrust",
            description="Apply linear thruster impulse to vehicle",
            parameters=[
                CapabilityParameter(name="vector_newtons", type_name="float", description="Thrust impulse"),
                CapabilityParameter(name="burn_time_sec", type_name="float", description="Duration", required=False, default=1.0),
            ],
            blast_radius=30,  # Medium risk
            handler=lambda p: {"status": "thrust_applied", "force": p["vector_newtons"] * p["burn_time_sec"]},
        )

    def tearDown(self) -> None:
        self.node.close()

    def test_as_mcp_tools_export(self) -> None:
        tools = self.node.as_mcp_tools()
        tool_names = [t["name"] for t in tools]

        self.assertIn("tandem_discover_capabilities", tool_names)
        self.assertIn("tandem_emergency_halt", tool_names)
        self.assertIn("tandem_release_halt", tool_names)
        self.assertIn("mesh_sim_apply_thrust", tool_names)

        # Inspect tool schema for mesh_sim_apply_thrust
        sim_tool = next(t for t in tools if t["name"] == "mesh_sim_apply_thrust")
        self.assertIn("Blast Radius: 30/100", sim_tool["description"])
        props = sim_tool["parameters"]["properties"]
        self.assertIn("vector_newtons", props)
        self.assertIn("burn_time_sec", props)
        self.assertEqual(sim_tool["parameters"]["required"], ["vector_newtons"])

    def test_execute_discovery_tool(self) -> None:
        res = self.node.execute_harness_tool("tandem_discover_capabilities", {})
        self.assertTrue(res["success"])
        cap_names = [c["name"] for c in res["capabilities"]]
        self.assertIn("sim.apply_thrust", cap_names)

    def test_execute_capability_tool(self) -> None:
        # Bind hand with G3_ARBITER_CRUISE (ceiling 70, allowing blast radius 30)
        self.node.register_hand(
            device_id="flight_stick",
            device_type="joystick",
            active_gear=AutonomyGear.G3_ARBITER_CRUISE,
        )

        res = self.node.execute_harness_tool(
            "mesh_sim_apply_thrust",
            {"vector_newtons": 500.0, "burn_time_sec": 2.5},
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["force"], 1250.0)
        self.assertIn("haptic_profile", res)
        # Blast radius 30 should produce amber lightbar
        self.assertEqual(res["haptic_profile"]["lightbar_rgb"], [255, 140, 0])

    def test_execute_emergency_halt_and_release_tools(self) -> None:
        halt_res = self.node.execute_harness_tool(
            "tandem_emergency_halt",
            {"reason": "Sim altitude alarm breached"},
        )
        self.assertTrue(halt_res["success"])
        self.assertEqual(halt_res["active_gear"], "G0_EBRAKE_STOP")

        # Subsequent attempts are blocked by E-Brake
        blocked_res = self.node.execute_harness_tool(
            "mesh_sim_apply_thrust",
            {"vector_newtons": 100.0},
        )
        self.assertFalse(blocked_res["success"])
        self.assertIn("EBrakeTriggeredError", blocked_res["error"])

        # Release halt via harness tool
        release_res = self.node.execute_harness_tool("tandem_release_halt", {})
        self.assertTrue(release_res["success"])
        self.assertEqual(release_res["active_gear"], "G2_SPORT_TACTILE")

        # Now bind hand or ratify to test dispatch
        self.node.register_hand(active_gear=AutonomyGear.G3_ARBITER_CRUISE)
        res_resumed = self.node.execute_harness_tool(
            "mesh_sim_apply_thrust",
            {"vector_newtons": 10.0, "burn_time_sec": 1.0},
        )
        self.assertTrue(res_resumed["success"])

    def test_ratification_haptic_feedback_in_harness(self) -> None:
        # In G2 (ceiling 20), sim.apply_thrust (blast radius 30) requires ratification
        res = self.node.execute_harness_tool(
            "mesh_sim_apply_thrust",
            {"vector_newtons": 50.0},
        )
        self.assertFalse(res["success"])
        self.assertIn("BlastRadiusRatificationRequired", res["error"])
        # Harness must receive haptic profile to transmit detent to controller
        self.assertIn("haptic_profile", res)
        self.assertEqual(res["haptic_profile"]["blast_radius"], 30)

    def test_capability_registration_update(self) -> None:
        self.node.register_capability("calc", "v1", handler=lambda p: 1)
        self.node.register_capability("calc", "v2", handler=lambda p: 2)
        resp = self.node.call("calc")
        self.assertTrue(resp.success)
        self.assertEqual(resp.data, 2)

    def test_deep_module_deletion_test(self) -> None:
        """
        Per /codebase-design:
        'The deletion test. Imagine deleting the module. If complexity vanishes,
         it was a pass-through. If complexity reappears across N callers, it was earning its keep.'

        Tandem packages:
          - Capability schema registry & type coercion
          - Monotonic taint lattice enforcement
          - Blast-radius risk categorization & detent thresholding
          - DualSense USB HID 0x02 report generation
          - Transport abstraction (memory/pipe/HTTP)
          - Emergency E-Brake broadcast
        All behind a single call: node.call(...) or node.execute_harness_tool(...).
        This proves the module is deep, providing immense leverage to callers.
        """
        from tandem.core.types import BlastRadiusRatificationRequired

        # Unratified attempt with blast radius 30 > ceiling 20 fails structurally
        with self.assertRaises(BlastRadiusRatificationRequired):
            self.node.call("sim.apply_thrust", {"vector_newtons": 250.0})

        # Squeezing the tactile hand detent ratifies the action
        resp = self.node.call(
            "sim.apply_thrust",
            {"vector_newtons": 250.0},
            ratified_by_hand=True,
        )
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["force"], 250.0)
        self.assertIsNotNone(resp.haptic_telemetry)
        self.assertGreater(resp.execution_time_ms, 0.0)


if __name__ == "__main__":
    unittest.main()

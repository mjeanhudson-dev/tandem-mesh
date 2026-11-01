"""
Unit tests for Tandem Capability Registry and Intent Router.
"""

from __future__ import annotations

import unittest

from tandem.core.registry import CapabilityRegistry
from tandem.core.router import IntentRouter
from tandem.core.types import (
    AppManifest,
    AutonomyGear,
    BlastRadiusRatificationRequired,
    Capability,
    CapabilityNotFoundError,
    CapabilityParameter,
    EBrakeTriggeredError,
    HandDevice,
    IntentRequest,
    SchemaValidationError,
    TaintLevel,
)


class TestRegistryAndRouter(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = CapabilityRegistry()
        self.router = IntentRouter(registry=self.registry)

        # Register CAD App
        self.cad_manifest = AppManifest(
            app_id="cad_engine",
            version="1.0.0",
            description="3D CAD and Mesh Generator",
            capabilities=[
                Capability(
                    name="cad.render_model",
                    description="Render a 3D geometry mesh",
                    parameters=[
                        CapabilityParameter(name="model_id", type_name="string", description="Model ID"),
                        CapabilityParameter(name="quality", type_name="int", description="Quality Level", required=False, default=1),
                    ],
                    blast_radius=15,  # Low risk (<20)
                    handler=lambda p: {"mesh_vertices": 1024, "model": p["model_id"], "quality": p["quality"]},
                ),
                Capability(
                    name="cad.export_production",
                    description="Export mesh to production fabrication server",
                    parameters=[
                        CapabilityParameter(name="model_id", type_name="string", description="Model ID"),
                    ],
                    blast_radius=75,  # High risk (>70)
                    handler=lambda p: {"status": "exported", "target": "cnc_mill_01"},
                ),
            ],
        )
        self.registry.register_app(self.cad_manifest)

    def test_app_and_capability_query(self) -> None:
        app = self.registry.get_app("cad_engine")
        self.assertIsNotNone(app)
        self.assertEqual(app.version, "1.0.0")

        cap = self.registry.get_capability("cad.render_model")
        self.assertEqual(cap.blast_radius, 15)

        with self.assertRaises(CapabilityNotFoundError):
            self.registry.get_capability("non_existent_capability")

    def test_successful_dispatch_within_blast_ceiling(self) -> None:
        req = IntentRequest(
            request_id="req_001",
            target_capability="cad.render_model",
            params={"model_id": "bracket_v2"},
            caller_app_id="agent_orchestrator",
            caller_taint=TaintLevel.INTERNAL_AGENT,
        )
        resp = self.router.dispatch(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["mesh_vertices"], 1024)
        self.assertEqual(resp.data["model"], "bracket_v2")
        self.assertEqual(resp.data["quality"], 1)  # Default applied
        self.assertIsNotNone(resp.haptic_telemetry)
        # Blast radius 15 is < 20: low risk, cyan lightbar
        self.assertEqual(resp.haptic_telemetry.lightbar_rgb, (0, 200, 255))

    def test_parameter_schema_validation_failure(self) -> None:
        req = IntentRequest(
            request_id="req_bad_param",
            target_capability="cad.render_model",
            params={"model_id": 9999},  # Expected string, got int
            caller_app_id="agent_orchestrator",
        )
        with self.assertRaises(SchemaValidationError):
            self.router.dispatch(req)

    def test_blast_radius_exceeding_gear_requires_ratification(self) -> None:
        # Hand in G2_SPORT_TACTILE has blast ceiling 20
        hand = HandDevice(device_id="dualsense_primary", device_type="dualsense", active_gear=AutonomyGear.G2_SPORT_TACTILE)
        self.router.register_hand(hand)

        # cad.export_production has blast radius 75 > 20
        req = IntentRequest(
            request_id="req_high_risk",
            target_capability="cad.export_production",
            params={"model_id": "bracket_v2"},
            caller_app_id="agent_orchestrator",
            ratified_by_hand=False,
        )

        # Must raise BlastRadiusRatificationRequired carrying haptic profile
        with self.assertRaises(BlastRadiusRatificationRequired) as ctx:
            self.router.dispatch(req)
        self.assertIsNotNone(ctx.exception.haptic_profile)
        self.assertEqual(ctx.exception.haptic_profile.blast_radius, 75)
        self.assertEqual(ctx.exception.haptic_profile.lightbar_rgb, (255, 20, 20))

        # Once ratified by hand detent squeeze, dispatch succeeds!
        hand.ratify()
        resp = self.router.dispatch(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["status"], "exported")
        # Blast radius 75 is high risk: crimson lightbar
        self.assertEqual(resp.haptic_telemetry.lightbar_rgb, (255, 20, 20))

        # Single-use protection: immediate second high-risk call must require ratification again
        with self.assertRaises(BlastRadiusRatificationRequired):
            self.router.dispatch(req)

    def test_ebrake_atomic_halt(self) -> None:
        ebrake_called = [False]

        def on_halt() -> None:
            ebrake_called[0] = True

        self.router.on_ebrake(on_halt)
        self.router.press_ebrake()

        self.assertTrue(ebrake_called[0])

        req = IntentRequest(
            request_id="req_during_ebrake",
            target_capability="cad.render_model",
            params={"model_id": "bracket_v2"},
            caller_app_id="agent",
        )
        with self.assertRaises(EBrakeTriggeredError):
            self.router.dispatch(req)

        # Release e-brake resumes operation
        self.router.release_ebrake()
        resp = self.router.dispatch(req)
        self.assertTrue(resp.success)


if __name__ == "__main__":
    unittest.main()

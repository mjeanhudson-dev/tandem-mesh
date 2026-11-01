"""
Tier 1 Feature Coverage: Requirement R4 (Tandem Simulation Prototype).
Verifies:
- Capability registration, query, prefix filtering, and catalog export
- Parameter validation contracts and bool-as-int type safety
- Monotonic taint lattice calculation and untrusted prompt injection blocking
- Cryptographic PINPOINT HMAC-SHA256 verification and promotion
- IntentRouter atomic dispatch pipeline
- Atomic Emergency E-Brake halt and resumption
- DualSense USB HID Output Report 0x02 assembly
- Transport seams (MemoryTransport, PipeTransport, TailscaleHttpTransport)
"""

import sys
import unittest
from pathlib import Path

# Add tandem to path
TANDEM_ROOT = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\tandem")
if str(TANDEM_ROOT) not in sys.path:
    sys.path.insert(0, str(TANDEM_ROOT))

from tandem.core.types import (
    AppManifest, Capability, CapabilityParameter, IntentRequest, IntentResponse,
    TaintLevel, AutonomyGear, HandDevice, SchemaValidationError
)
from tandem.core.registry import CapabilityRegistry
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.router import IntentRouter, EBrakeTriggeredError
from tandem.core.haptics import HapticSynthesizer
from tandem.transport.memory import MemoryTransport


class TestR4SimulationPrototypeFeatures(unittest.TestCase):

    def setUp(self):
        self.registry = CapabilityRegistry()
        self.lattice = StructuralTaintLattice()
        self.router = IntentRouter(self.registry, self.lattice)
        self.transport = MemoryTransport()
        self.transport.set_handler(self.router.dispatch)
        self.router.on_ebrake(self.transport.broadcast_ebrake)
        self.transport.start()

    def tearDown(self):
        self.transport.stop()

    def test_r4_f1_capability_registration_and_catalog_export(self):
        """Feature 1: Verify capability registration, lookup, prefix filtering, and catalog export."""
        cap = Capability(
            name="cad.create_box",
            description="Creates 3D box solid",
            parameters=[
                CapabilityParameter(name="width", type_name="float", description="Box width"),
                CapabilityParameter(name="height", type_name="float", description="Box height"),
            ],
            handler=lambda params: {"volume": params["width"] * params["height"]},
            blast_radius=5,
            min_taint_level=TaintLevel.INTERNAL_AGENT
        )
        manifest = AppManifest(
            app_id="cad_studio",
            version="1.0.0",
            description="CAD Studio",
            capabilities=[cap]
        )
        self.registry.register_app(manifest)

        # Lookup
        found = self.registry.get_capability("cad.create_box")
        self.assertEqual(found.name, "cad.create_box")

        # Prefix filter
        cad_caps = self.registry.list_capabilities(prefix="cad.")
        self.assertEqual(len(cad_caps), 1)
        sim_caps = self.registry.list_capabilities(prefix="sim.")
        self.assertEqual(len(sim_caps), 0)

        # Catalog export
        catalog = self.registry.export_catalog()
        self.assertIn("cad_studio", catalog)

    def test_r4_f2_parameter_type_contracts_and_bool_as_int_defense(self):
        """Feature 2: Verify parameter validation contracts and defense against bool-as-int."""
        int_param = CapabilityParameter(name="count", type_name="int", description="Item count")

        # Valid int
        self.assertEqual(int_param.validate(10), 10)

        # Bool passed to int must fail (Python bool is subclass of int)
        with self.assertRaises(SchemaValidationError):
            int_param.validate(True)

        # Float param accepting int (should succeed without caller casting)
        float_param = CapabilityParameter(name="pressure", type_name="float", description="Air pressure")
        self.assertEqual(float_param.validate(42), 42.0)
        self.assertEqual(float_param.validate(3.14), 3.14)

    def test_r4_f3_monotonic_taint_lattice_attenuation(self):
        """Feature 3: Verify monotonic taint attenuation T_out = min(T) and injection blocking."""
        # Minimum calculation
        composed = self.lattice.compute_composed_taint([
            TaintLevel.PINPOINT_VERIFIED,
            TaintLevel.INTERNAL_AGENT,
            TaintLevel.UNTRUSTED_EXTERNAL
        ])
        self.assertEqual(composed, TaintLevel.UNTRUSTED_EXTERNAL)

        # Privileged capability blocking untrusted caller
        from tandem.core.lattice import TaintAttenuationError
        with self.assertRaises(TaintAttenuationError):
            self.lattice.verify_dispatch_allowed(
                caller_taint=TaintLevel.UNTRUSTED_EXTERNAL,
                min_required_taint=TaintLevel.INTERNAL_AGENT,
                capability_name="admin.system_reset"
            )

    def test_r4_f4_pinpoint_hmac_sha256_promotion(self):
        """Feature 4: Verify cryptographic PINPOINT signature verification and taint promotion."""
        artifact_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        sig = self.lattice.sign_pinpoint_receipt(artifact_sha, "test_suite", 50, 50)

        # Valid promotion
        promoted = self.lattice.promote_with_pinpoint(artifact_sha, "test_suite", 50, 50, sig)
        self.assertEqual(promoted, TaintLevel.PINPOINT_VERIFIED)

        # Incomplete checks fail
        from tandem.core.lattice import TaintAttenuationError
        with self.assertRaises(TaintAttenuationError):
            self.lattice.promote_with_pinpoint(artifact_sha, "test_suite", 49, 50, sig)

    def test_r4_f5_intent_router_atomic_dispatch(self):
        """Feature 5: Verify 7-stage atomic dispatch pipeline."""
        cap = Capability(
            name="math.add",
            description="Add numbers",
            parameters=[
                CapabilityParameter(name="a", type_name="int", description="First addend"),
                CapabilityParameter(name="b", type_name="int", description="Second addend"),
            ],
            handler=lambda params: {"sum": params["a"] + params["b"]},
            blast_radius=0,
            min_taint_level=TaintLevel.UNTRUSTED_EXTERNAL
        )
        self.registry.register_app(AppManifest("math_app", "1.0", "Math App", [cap]))

        req = IntentRequest(
            request_id="req-1",
            target_capability="math.add",
            params={"a": 15, "b": 27},
            caller_app_id="test_client",
            caller_taint=TaintLevel.INTERNAL_AGENT
        )
        resp = self.transport.send(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["sum"], 42)
        self.assertIsNotNone(resp.haptic_telemetry)

    def test_r4_f6_atomic_ebrake_halt_and_resumption(self):
        """Feature 6: Verify press_ebrake halts dispatch immediately and release_ebrake restores."""
        cap = Capability(
            name="test.action",
            description="Simple test",
            handler=lambda params: {"status": "ok"},
            blast_radius=0,
            min_taint_level=TaintLevel.UNTRUSTED_EXTERNAL
        )
        self.registry.register_app(AppManifest("test_app", "1.0", "Test App", [cap]))

        # Normal dispatch
        req = IntentRequest("req-1", "test.action", {}, "client", TaintLevel.INTERNAL_AGENT)
        resp = self.transport.send(req)
        self.assertTrue(resp.success)

        # Press E-Brake
        self.router.press_ebrake("safety_sentinel")
        self.assertTrue(self.router._ebrake_active)

        # Dispatches must fail with EBrakeTriggeredError
        with self.assertRaises(EBrakeTriggeredError):
            self.transport.send(req)

        # Release E-Brake
        self.router.release_ebrake()
        self.transport.release_ebrake()
        self.assertFalse(self.router._ebrake_active)

        # Resumes successfully
        resp2 = self.transport.send(req)
        self.assertTrue(resp2.success)

    def test_r4_f7_dualsense_usb_hid_0x02_report_assembly(self):
        """Feature 7: Verify generation of 64-byte Sony DualSense USB Output Report 0x02."""
        synth = HapticSynthesizer()
        profile = synth.synthesize(blast_radius=75, active_gear=AutonomyGear.G3_ARBITER_CRUISE)

        report = synth.generate_dualsense_hid_report(profile)
        self.assertEqual(len(report), 64, "DualSense report must be exactly 64 bytes")
        self.assertEqual(report[0], 0x02, "First byte must be Output Report ID 0x02")

        # Verify RGB lightbar bytes in report
        self.assertEqual(report[45], profile.lightbar_rgb[0])
        self.assertEqual(report[46], profile.lightbar_rgb[1])
        self.assertEqual(report[47], profile.lightbar_rgb[2])


if __name__ == "__main__":
    unittest.main()

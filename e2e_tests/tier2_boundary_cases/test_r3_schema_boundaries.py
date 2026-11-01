"""
Tier 2 Boundary & Corner Cases: Requirement R3 (Tandem Architecture & Schema Boundaries).
Tests manifest boundary validation, parameter contract boundaries, extreme blast radius values,
and autonomy gear ceilings.
"""

import sys
import unittest
from pathlib import Path

# Add tandem and e2e_tests root to sys.path
E2E_ROOT = Path(__file__).resolve().parent.parent
TANDEM_ROOT = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\tandem")
for p in [str(E2E_ROOT), str(TANDEM_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from tandem.core.types import (
    AppManifest, Capability, CapabilityParameter, AutonomyGear,
    SchemaValidationError, TaintLevel
)
from tandem.core.haptics import HapticSynthesizer


class TestR3SchemaBoundaries(unittest.TestCase):

    def test_r3_b1_manifest_missing_required_capability_field(self):
        """Boundary 1: AppManifest get_capability on non-existent capability returns None."""
        manifest = AppManifest(
            app_id="boundary_app",
            version="1.0.0",
            description="Testing manifest boundaries",
            capabilities=[]
        )
        self.assertIsNone(manifest.get_capability("non_existent_cap"))

    def test_r3_b2_parameter_unsupported_type_fallback(self):
        """Boundary 2: Parameter with unknown type string falls back to object validation."""
        param = CapabilityParameter(name="custom_blob", type_name="unknown_format", description="Unknown type")
        # Since unknown falls back to object, it accepts arbitrary values
        val = {"custom": 123}
        self.assertEqual(param.validate(val), val)

    def test_r3_b3_haptic_synthesizer_clamps_negative_blast_radius(self):
        """Boundary 3: HapticSynthesizer clamps negative blast radius to 0."""
        synth = HapticSynthesizer()
        profile = synth.synthesize(blast_radius=-50, active_gear=AutonomyGear.G2_SPORT_TACTILE)
        self.assertEqual(profile.blast_radius, 0)
        # Should produce Low Risk (Cyan lightbar: 0, 200, 255)
        self.assertEqual(profile.lightbar_rgb, (0, 200, 255))

    def test_r3_b4_haptic_synthesizer_clamps_excessive_blast_radius(self):
        """Boundary 4: HapticSynthesizer clamps blast radius > 100 to 100."""
        synth = HapticSynthesizer()
        profile = synth.synthesize(blast_radius=999, active_gear=AutonomyGear.G2_SPORT_TACTILE)
        self.assertEqual(profile.blast_radius, 100)
        # Should produce High Risk (Crimson lightbar: 255, 20, 20)
        self.assertEqual(profile.lightbar_rgb, (255, 20, 20))

    def test_r3_b5_autonomy_gear_boundary_ceilings(self):
        """Boundary 5: AutonomyGear enum enforces strict blast radius ceilings."""
        self.assertEqual(AutonomyGear.G0_EBRAKE_STOP.blast_ceiling, 0)
        self.assertEqual(AutonomyGear.G1_CLUTCH_MANUAL.blast_ceiling, 0)
        self.assertEqual(AutonomyGear.G2_SPORT_TACTILE.blast_ceiling, 20)
        self.assertEqual(AutonomyGear.G3_ARBITER_CRUISE.blast_ceiling, 70)
        self.assertEqual(AutonomyGear.G4_AUTONOMOUS_MESH.blast_ceiling, 90)

    def test_r3_b6_capability_default_values_on_none_input(self):
        """Boundary 6: Optional parameter returns default value when missing from input."""
        opt_param = CapabilityParameter(
            name="retries",
            type_name="int",
            description="Retry count",
            required=False,
            default=3
        )
        cap = Capability(
            name="test.retry_cap",
            description="Testing defaults",
            parameters=[opt_param],
            handler=lambda p: p
        )
        validated = cap.validate_params({})
        self.assertEqual(validated["retries"], 3)


if __name__ == "__main__":
    unittest.main()

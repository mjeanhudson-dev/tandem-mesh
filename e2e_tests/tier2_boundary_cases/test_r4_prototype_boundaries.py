"""
Tier 2 Boundary & Corner Cases: Requirement R4 (Tandem Prototype & Kinematics Boundaries).
Tests bool-as-int type safety, menu deadzone boundaries, driving latch thresholds,
mechanical detent ratification, sagittal recline gravity decoupling, and TTL expiration.
"""

import sys
import time
import unittest
from pathlib import Path

# Add tandem and e2e_tests root to sys.path
E2E_ROOT = Path(__file__).resolve().parent.parent
TANDEM_ROOT = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\tandem")
for p in [str(E2E_ROOT), str(TANDEM_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from tandem.core.types import (
    CapabilityParameter, HandDevice, SchemaValidationError, AutonomyGear
)
from tandem.core.dualsense import DualSenseKinematics, DualSenseTriggerFilter


class TestR4PrototypeBoundaries(unittest.TestCase):

    def test_r4_b1_bool_as_int_rejection(self):
        """Boundary 1: Parameter typed as int rejects True and False (bool-as-int protection)."""
        param = CapabilityParameter(name="iterations", type_name="int", description="Iterations")
        with self.assertRaises(SchemaValidationError):
            param.validate(True)
        with self.assertRaises(SchemaValidationError):
            param.validate(False)

    def test_r4_b2_int_to_float_acceptance(self):
        """Boundary 2: Parameter typed as float accepts integer without caller casting."""
        param = CapabilityParameter(name="scale", type_name="float", description="Scale factor")
        result = param.validate(10)
        self.assertIsInstance(result, (int, float))
        self.assertEqual(result, 10.0)

    def test_r4_b3_menu_deadzone_counts_boundary(self):
        """Boundary 3: Rule 3 deadzone: counts 0-15 swallowed to 0; count 16 preserved."""
        # 0 to 15 swallowed
        for count in [0, 5, 7, 10, 12, 15]:
            self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(count, deadzone=15), 0, f"Count {count} must be swallowed")

        # 16 breaks deadzone
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(16, deadzone=15), 16)
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(255, deadzone=15), 255)

    def test_r4_b4_driving_latch_threshold_boundary(self):
        """Boundary 4: Rule 3 latch: count 35 does NOT latch; count 36 latches driving mode."""
        # Not latched initially, 35 counts throttle, 0 rumble -> remains False
        self.assertFalse(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=35, game_rumble=0, currently_latched=False))

        # 36 counts throttle -> latches True
        self.assertTrue(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=36, game_rumble=0, currently_latched=False))

        # Rumble > 0 also latches regardless of throttle
        self.assertTrue(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=0, game_rumble=1, currently_latched=False))

    def test_r4_b5_detent_ratification_counts_boundary(self):
        """Boundary 5: HandDevice trigger: count 127 does NOT ratify; count 128 ratifies."""
        dev = HandDevice(device_id="dualsense_01", device_type="dualsense")

        # 127 counts (just below 128 mechanical detent)
        ratified_127 = dev.evaluate_trigger(trigger_counts=127, is_menu=False, detent_threshold=128)
        self.assertFalse(ratified_127)
        self.assertFalse(dev.is_ratification_fresh())

        # 128 counts (exact mechanical detent threshold)
        ratified_128 = dev.evaluate_trigger(trigger_counts=128, is_menu=False, detent_threshold=128)
        self.assertTrue(ratified_128)
        self.assertTrue(dev.is_ratification_fresh())

    def test_r4_b6_sagittal_recline_lateral_gravity_decoupling(self):
        """Boundary 6: Rule 4: Pitch |theta| > 30 deg completely decouples lateral gravity ax."""
        # At pitch = -45 deg, ax = 9.8 m/s^2 must produce identical output to ax = 0.0 m/s^2
        omega_z, omega_y = 10.0, 5.0
        pitch_reclined = -45.0

        steering_with_gravity = DualSenseKinematics.project_sagittal_steering(
            omega_z=omega_z, omega_y=omega_y, theta_pitch_deg=pitch_reclined, ax=9.8
        )
        steering_without_gravity = DualSenseKinematics.project_sagittal_steering(
            omega_z=omega_z, omega_y=omega_y, theta_pitch_deg=pitch_reclined, ax=0.0
        )
        self.assertAlmostEqual(steering_with_gravity, steering_without_gravity, places=6)

    def test_r4_b7_single_use_ratification_consumption(self):
        """Boundary 7: consume_ratification immediately zeroes timestamp preventing replay."""
        dev = HandDevice(device_id="dualsense_02", device_type="dualsense")
        dev.evaluate_trigger(trigger_counts=150, is_menu=False)
        self.assertTrue(dev.is_ratification_fresh())

        # Single-use consumption
        dev.consume_ratification()
        self.assertFalse(dev.is_ratification_fresh(), "Ratification must be consumed and invalid")

    def test_r4_b8_sliding_ttl_window_expiration(self):
        """Boundary 8: Ratification older than TTL window returns expired."""
        dev = HandDevice(device_id="dualsense_03", device_type="dualsense")
        # Stamp a timestamp 10 seconds in the past
        dev.last_ratification_timestamp = time.time() - 10.0

        # With default TTL of 5.0s, it must be expired
        self.assertFalse(dev.is_ratification_fresh(ttl_seconds=5.0))


if __name__ == "__main__":
    unittest.main()

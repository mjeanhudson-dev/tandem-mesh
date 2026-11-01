"""
Unit and mathematical tests for DualSense Gyro & Racing Architecture Rules.

Verifies:
  Rule 1: Inverse pre-compensation for non-linear game curves.
  Rule 2: 200 ms C^2 smootherstep transition blend.
  Rule 3: Menu trigger isolation & 15-count deadzone (swallowing resting finger float 7-12 counts).
  Rule 4: Lap & recline immunity with sagittal plane projection and gravity decoupling.
"""

from __future__ import annotations

import math
import unittest

from tandem.core.dualsense import DualSenseKinematics, DualSenseTriggerFilter
from tandem.core.types import AutonomyGear, HandDevice


class TestDualSenseRules(unittest.TestCase):
    def test_rule1_inverse_precompensation(self) -> None:
        """Rule 1: X_proxy = d_game + (1 - d_game) * sqrt(|x|) * sgn(x)."""
        d_game = 0.20

        # Zero remains zero
        self.assertEqual(DualSenseKinematics.inverse_precompensation(0.0, d_game), 0.0)

        # Full throw (1.0 and -1.0)
        self.assertAlmostEqual(DualSenseKinematics.inverse_precompensation(1.0, d_game), 1.0)
        self.assertAlmostEqual(DualSenseKinematics.inverse_precompensation(-1.0, d_game), -1.0)

        # Half throw (0.25 -> sqrt(0.25) = 0.5; 0.20 + 0.80 * 0.5 = 0.60)
        expected_pos = 0.20 + 0.80 * 0.5
        self.assertAlmostEqual(DualSenseKinematics.inverse_precompensation(0.25, d_game), expected_pos)
        self.assertAlmostEqual(DualSenseKinematics.inverse_precompensation(-0.25, d_game), -expected_pos)

    def test_rule2_smootherstep_blend(self) -> None:
        """Rule 2: 200 ms C^2 Smootherstep blend S(t) = 6t^5 - 15t^4 + 10t^3."""
        # Boundary values
        self.assertEqual(DualSenseKinematics.smootherstep(0.0), 0.0)
        self.assertEqual(DualSenseKinematics.smootherstep(1.0), 1.0)
        self.assertEqual(DualSenseKinematics.smootherstep(-0.5), 0.0)
        self.assertEqual(DualSenseKinematics.smootherstep(1.5), 1.0)

        # Midpoint: S(0.5) = 6*(1/32) - 15*(1/16) + 10*(1/8) = 6/32 - 30/32 + 40/32 = 16/32 = 0.5
        self.assertAlmostEqual(DualSenseKinematics.smootherstep(0.5), 0.5)

        # Frame 0 transition blend softly zeroes (0.0)
        val_f0 = DualSenseKinematics.apply_transition_blend(elapsed_sec=0.0, duration_sec=0.2, current_value=100.0)
        self.assertEqual(val_f0, 0.0)

        # 100 ms (halfway through 200 ms transition)
        val_mid = DualSenseKinematics.apply_transition_blend(elapsed_sec=0.1, duration_sec=0.2, current_value=100.0)
        self.assertAlmostEqual(val_mid, 50.0)

        # 200 ms (transition complete)
        val_end = DualSenseKinematics.apply_transition_blend(elapsed_sec=0.2, duration_sec=0.2, current_value=100.0)
        self.assertAlmostEqual(val_end, 100.0)

    def test_rule3_menu_trigger_deadzone_and_driving_latch(self) -> None:
        """
        Rule 3: 15-count deadzone in menus to swallow resting finger float (7-12 counts).
        Driving mode latched by R2 > 35 or game rumble > 0.
        """
        # Resting finger float (7-12 counts) swallowed to 0
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(0), 0)
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(7), 0)
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(10), 0)
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(12), 0)
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(15), 0)

        # Active input above 15 counts passes through
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(16), 16)
        self.assertEqual(DualSenseTriggerFilter.apply_menu_deadzone(100), 100)

        # Driving latch evaluation
        self.assertFalse(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=20, game_rumble=0))
        self.assertTrue(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=36, game_rumble=0))
        self.assertTrue(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=10, game_rumble=50))

        # Once latched, stays latched
        self.assertTrue(DualSenseTriggerFilter.evaluate_driving_latch(r2_counts=0, game_rumble=0, currently_latched=True))

    def test_rule4_lap_and_recline_immunity(self) -> None:
        """
        Rule 4: Sagittal plane projection:
          omega_roll = -(omega_z * cos(theta_pitch) + omega_y * sin(theta_pitch))
        Decouple lateral accelerometer gravity (ax) when |theta_pitch| > 30°.
        """
        # Pure upright position (pitch = 0°) -> omega_roll = -omega_z
        roll_0 = DualSenseKinematics.project_sagittal_steering(omega_z=10.0, omega_y=5.0, theta_pitch_deg=0.0)
        self.assertAlmostEqual(roll_0, -10.0)

        # Reclined at -45° (common natural driving posture between -15° and -75°)
        # cos(-45°) = sin(-45°) = 1/sqrt(2) approx 0.7071
        theta = -45.0
        rad = math.radians(theta)
        expected = -(10.0 * math.cos(rad) + 5.0 * math.sin(rad))
        roll_45 = DualSenseKinematics.project_sagittal_steering(omega_z=10.0, omega_y=5.0, theta_pitch_deg=-45.0)
        self.assertAlmostEqual(roll_45, expected)

        # Reclined (|theta| > 30°): lateral accelerometer (ax) MUST be decoupled
        roll_with_ax = DualSenseKinematics.project_sagittal_steering(
            omega_z=10.0, omega_y=5.0, theta_pitch_deg=-45.0, ax=9.8
        )
        self.assertEqual(roll_with_ax, roll_45)  # ax completely ignored when reclined

        # Upright (|theta| <= 30°): ax is blended slightly for gravity anchoring
        roll_upright_no_ax = DualSenseKinematics.project_sagittal_steering(
            omega_z=10.0, omega_y=5.0, theta_pitch_deg=10.0, ax=0.0
        )
        roll_upright_with_ax = DualSenseKinematics.project_sagittal_steering(
            omega_z=10.0, omega_y=5.0, theta_pitch_deg=10.0, ax=2.0
        )
        self.assertNotEqual(roll_upright_no_ax, roll_upright_with_ax)

    def test_hand_device_trigger_ratification_integration(self) -> None:
        hand = HandDevice(device_id="dualsense_wheel", device_type="dualsense")

        # Resting finger float in menu does not ratify
        ratified_float = hand.evaluate_trigger(trigger_counts=10, is_menu=True)
        self.assertFalse(ratified_float)
        self.assertFalse(hand.is_ratification_fresh())

        # Pulling trigger to 50 counts latches driving mode, but below detent (128) does not ratify
        ratified_throttle = hand.evaluate_trigger(trigger_counts=50, is_menu=False)
        self.assertFalse(ratified_throttle)
        self.assertTrue(hand.is_driving_latched)
        self.assertFalse(hand.is_ratification_fresh())

        # Squeezing past mechanical detent threshold (>= 128) immediately ratifies
        ratified_detent = hand.evaluate_trigger(trigger_counts=180, is_menu=False)
        self.assertTrue(ratified_detent)
        self.assertTrue(hand.is_ratification_fresh())


if __name__ == "__main__":
    unittest.main()

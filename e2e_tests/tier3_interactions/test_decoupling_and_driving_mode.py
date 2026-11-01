"""
Tier 3 Cross-Feature Interaction: DualSense Deadzone + Driving Latch + Recline Decoupling + Haptic Telemetry.
Verifies pairwise interaction between:
- Frontend menu trigger deadzone (Rule 3)
- Dynamic driving mode latching
- Sagittal steering recline projection & lateral gravity decoupling (Rule 4)
- DualSense USB HID 0x02 Output Report telemetry generation
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

from tandem.core.types import HandDevice, AutonomyGear
from tandem.core.dualsense import DualSenseKinematics, DualSenseTriggerFilter
from tandem.core.haptics import HapticSynthesizer


class TestDecouplingAndDrivingMode(unittest.TestCase):

    def test_i1_menu_isolation_transitions_to_latched_driving_and_recline_steering(self):
        """Interaction: Menu deadzone swallows resting float -> throttle latches driving -> recline decouples gravity."""
        dev = HandDevice(device_id="dualsense_rig", device_type="dualsense")

        # 1. In frontend menu, resting finger float (10 counts) must be swallowed and driving mode unlatched
        ratified = dev.evaluate_trigger(trigger_counts=10, is_menu=True)
        self.assertFalse(ratified)
        self.assertFalse(dev.is_driving_latched, "Resting float in menu must not latch driving mode")

        # 2. Driver pulls throttle to 80 counts (> 35 counts) -> latches driving mode
        dev.evaluate_trigger(trigger_counts=80, is_menu=False)
        self.assertTrue(dev.is_driving_latched, "Throttle > 35 must latch driving mode")

        # 3. Driving in natural reclined cockpit posture (pitch = -50 degrees) with cornering g-force (ax = 12.5 m/s^2)
        # Lateral gravity must be completely decoupled (|theta| > 30 deg)
        omega_z, omega_y = 15.0, 8.0
        pitch_angle = -50.0

        steering_loaded = DualSenseKinematics.project_sagittal_steering(
            omega_z=omega_z, omega_y=omega_y, theta_pitch_deg=pitch_angle, ax=12.5
        )
        steering_unloaded = DualSenseKinematics.project_sagittal_steering(
            omega_z=omega_z, omega_y=omega_y, theta_pitch_deg=pitch_angle, ax=0.0
        )
        self.assertAlmostEqual(steering_loaded, steering_unloaded, places=6,
                               msg="Reclined steering must have 100% lateral gravity decoupling")

        # 4. Synthesize DualSense Output Report ID 0x02 during high-speed turn (blast radius 80)
        synth = HapticSynthesizer()
        profile = synth.synthesize(blast_radius=80, active_gear=AutonomyGear.G2_SPORT_TACTILE)
        report = synth.generate_dualsense_hid_report(profile)

        self.assertEqual(len(report), 64)
        self.assertEqual(report[0], 0x02)
        # Crimson lightbar on high-risk profile
        self.assertEqual(profile.lightbar_rgb, (255, 20, 20))


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for App-to-Hand (A2H) Blast-Radius Haptic Synthesizer and DualSense HID packets.
"""

from __future__ import annotations

import unittest

from tandem.core.haptics import HapticSynthesizer
from tandem.core.types import AutonomyGear


class TestAppToHandHaptics(unittest.TestCase):
    def test_low_risk_haptic_profile(self) -> None:
        profile = HapticSynthesizer.synthesize(blast_radius=10, active_gear=AutonomyGear.G2_SPORT_TACTILE)
        self.assertEqual(profile.blast_radius, 10)
        self.assertEqual(profile.lightbar_rgb, (0, 200, 255))  # Cyan
        self.assertEqual(profile.left_trigger_mode, 0x00)
        self.assertEqual(profile.right_trigger_mode, 0x00)
        self.assertEqual(profile.motor_rumble_left, 0)
        self.assertEqual(profile.motor_rumble_right, 0)
        self.assertEqual(profile.mobile_vibration_ms, 0)

    def test_medium_risk_haptic_profile(self) -> None:
        profile = HapticSynthesizer.synthesize(blast_radius=45, active_gear=AutonomyGear.G2_SPORT_TACTILE)
        self.assertEqual(profile.blast_radius, 45)
        self.assertEqual(profile.lightbar_rgb, (255, 140, 0))  # Amber
        self.assertEqual(profile.left_trigger_mode, 0x00)
        self.assertEqual(profile.right_trigger_mode, 0x05)  # Spring Detent
        self.assertGreater(profile.motor_rumble_right, 0)
        self.assertGreater(profile.mobile_vibration_ms, 0)

    def test_high_risk_haptic_profile(self) -> None:
        profile = HapticSynthesizer.synthesize(blast_radius=85, active_gear=AutonomyGear.G2_SPORT_TACTILE)
        self.assertEqual(profile.blast_radius, 85)
        self.assertEqual(profile.lightbar_rgb, (255, 20, 20))  # Crimson
        self.assertEqual(profile.left_trigger_mode, 0x26)  # 40Hz warning judder
        self.assertEqual(profile.right_trigger_mode, 0x21)  # Static resistance detent
        self.assertEqual(profile.motor_rumble_left, 120)
        self.assertEqual(profile.motor_rumble_right, 180)
        self.assertEqual(profile.mobile_vibration_ms, 250)

    def test_ebrake_haptic_profile(self) -> None:
        profile = HapticSynthesizer.synthesize(blast_radius=10, ebrake_active=True)
        self.assertEqual(profile.lightbar_rgb, (255, 0, 0))  # Full Red
        self.assertEqual(profile.left_trigger_mode, 0x26)
        self.assertEqual(profile.right_trigger_mode, 0x21)
        self.assertEqual(profile.motor_rumble_left, 255)
        self.assertEqual(profile.motor_rumble_right, 255)
        self.assertEqual(profile.mobile_vibration_ms, 500)

    def test_dualsense_hid_report_encoding(self) -> None:
        profile = HapticSynthesizer.synthesize(blast_radius=80)
        hid_report = HapticSynthesizer.generate_dualsense_hid_report(profile)

        # Invariants of Sony DualSense USB Output Report 0x02
        self.assertEqual(len(hid_report), 64)
        self.assertEqual(hid_report[0], 0x02)  # Report ID
        self.assertEqual(hid_report[1], 0xFF)  # Full update flag
        self.assertEqual(hid_report[2], 0x17)  # Trigger subflag

        # Motor rumble positions
        self.assertEqual(hid_report[3], profile.motor_rumble_right)
        self.assertEqual(hid_report[4], profile.motor_rumble_left)

        # Trigger modes
        self.assertEqual(hid_report[11], profile.right_trigger_mode)
        self.assertEqual(hid_report[22], profile.left_trigger_mode)

        # Lightbar setup flag (byte 42 == 0x02 to enable LED update on Sony hardware)
        self.assertEqual(hid_report[42], 0x02)

        # Lightbar RGB positions (bytes 45, 46, 47)
        r, g, b = profile.lightbar_rgb
        self.assertEqual(hid_report[45], r)
        self.assertEqual(hid_report[46], g)
        self.assertEqual(hid_report[47], b)

    def test_haptic_profile_serialization_round_trip(self) -> None:
        profile = HapticSynthesizer.synthesize(blast_radius=85)
        d = profile.to_dict()
        reconstructed = profile.from_dict(d)

        self.assertEqual(reconstructed.blast_radius, profile.blast_radius)
        self.assertEqual(reconstructed.lightbar_rgb, profile.lightbar_rgb)
        self.assertEqual(reconstructed.left_trigger_mode, profile.left_trigger_mode)
        self.assertEqual(reconstructed.left_trigger_params, profile.left_trigger_params)
        self.assertEqual(reconstructed.right_trigger_mode, profile.right_trigger_mode)
        self.assertEqual(reconstructed.right_trigger_params, profile.right_trigger_params)
        self.assertEqual(reconstructed.motor_rumble_left, profile.motor_rumble_left)
        self.assertEqual(reconstructed.motor_rumble_right, profile.motor_rumble_right)
        self.assertEqual(reconstructed.mobile_vibration_ms, profile.mobile_vibration_ms)


if __name__ == "__main__":
    unittest.main()

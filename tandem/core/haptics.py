"""
App-to-Hand (A2H) Blast-Radius Haptic Synthesizer.

Translates semantic risk (blast radius B(a) in [0, 100]) into physical hardware
friction and telemetry across:
  - Sony DualSense Wireless Controllers (USB HID Output Report 0x02 adaptive triggers)
  - Mobile Phones (iOS / Android Haptic Vibration Webhooks)
  - Tactile Sliders & Foot Pedals
"""

from __future__ import annotations

import math
from typing import Optional

from tandem.core.types import AutonomyGear, HapticProfile


class HapticSynthesizer:
    """
    Synthesizes physical tactile resistance profiles from action risk metrics.
    """

    @classmethod
    def synthesize(
        cls,
        blast_radius: int,
        active_gear: AutonomyGear = AutonomyGear.G2_SPORT_TACTILE,
        ebrake_active: bool = False,
    ) -> HapticProfile:
        """
        Generate complete HapticProfile for given blast radius and gear.

        Risk tiers:
          - E-Brake Active: Pulsing Crimson (255, 0, 0), Active 40Hz Judder, Hard Trigger Lock.
          - Low Risk (0-19): Pure Cyan (0, 200, 255), Zero resistance, Smooth travel.
          - Medium Risk (20-69): Amber (255, 140, 0), Soft Spring Detent (mode 0x05).
          - High Risk (70-100): Crimson (255, 20, 20), Hard Static Stop (mode 0x21) + Judder.
        """
        blast_radius = max(0, min(100, blast_radius))

        if ebrake_active or active_gear == AutonomyGear.G0_EBRAKE_STOP:
            return HapticProfile(
                blast_radius=blast_radius,
                lightbar_rgb=(255, 0, 0),
                left_trigger_mode=0x26,  # Active warning judder
                left_trigger_params=bytes([0x08, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00]),
                right_trigger_mode=0x21,  # Hard static resistance detent
                right_trigger_params=bytes([0x01, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00]),
                motor_rumble_left=255,
                motor_rumble_right=255,
                mobile_vibration_ms=500,
            )

        if blast_radius < 20:
            # Low Risk: Read/Inspect
            # Cyan lightbar, zero trigger resistance (mode 0x00)
            return HapticProfile(
                blast_radius=blast_radius,
                lightbar_rgb=(0, 200, 255),
                left_trigger_mode=0x00,
                left_trigger_params=bytes(7),
                right_trigger_mode=0x00,
                right_trigger_params=bytes(7),
                motor_rumble_left=0,
                motor_rumble_right=0,
                mobile_vibration_ms=0,
            )
        elif blast_radius < 70:
            # Medium Risk: Local workspace mutations
            # Amber lightbar, soft spring resistance (mode 0x05)
            # Scaled resistance based on blast radius
            force = int(50 + (blast_radius - 20) * 3)  # 50 to 200
            force = min(255, force)
            return HapticProfile(
                blast_radius=blast_radius,
                lightbar_rgb=(255, 140, 0),
                left_trigger_mode=0x00,
                left_trigger_params=bytes(7),
                right_trigger_mode=0x05,  # Variable spring detent
                right_trigger_params=bytes([0x00, force, 0x00, 0x00, 0x00, 0x00, 0x00]),
                motor_rumble_left=0,
                motor_rumble_right=int(force * 0.3),
                mobile_vibration_ms=50,
            )
        else:
            # High Risk: Egress, deletions, credentials, production mutations
            # Crimson lightbar, hard static detent on Right Trigger + active judder on Left Trigger
            return HapticProfile(
                blast_radius=blast_radius,
                lightbar_rgb=(255, 20, 20),
                left_trigger_mode=0x26,  # 40Hz active judder
                left_trigger_params=bytes([0x04, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00]),
                right_trigger_mode=0x21,  # Hard detent at position 30%
                right_trigger_params=bytes([0x03, 0xE0, 0x00, 0x00, 0x00, 0x00, 0x00]),
                motor_rumble_left=120,
                motor_rumble_right=180,
                mobile_vibration_ms=250,
            )

    @classmethod
    def generate_dualsense_hid_report(cls, profile: HapticProfile) -> bytes:
        """
        Builds standard 64-byte Sony DualSense USB Output Report (Report ID 0x02).
        Conforms strictly to DualSense reverse-engineered protocol.
        """
        report = bytearray(64)
        report[0] = 0x02  # Report ID
        report[1] = 0xFF  # Valid flag: lightbar + haptics + triggers + motors
        report[2] = 0x17  # Valid flag sub-bits (triggers active)

        # Motor rumble
        report[3] = profile.motor_rumble_right & 0xFF  # Right small motor
        report[4] = profile.motor_rumble_left & 0xFF   # Left heavy motor

        # Right Trigger Adaptive Force
        report[11] = profile.right_trigger_mode & 0xFF
        for i, b in enumerate(profile.right_trigger_params[:7]):
            report[12 + i] = b

        # Left Trigger Adaptive Force
        report[22] = profile.left_trigger_mode & 0xFF
        for i, b in enumerate(profile.left_trigger_params[:7]):
            report[23 + i] = b

        # Lightbar Setup Flag (0x02 enables RGB LED lightbar updates on Sony hardware)
        report[42] = 0x02

        # Lightbar RGB
        r, g, b = profile.lightbar_rgb
        report[45] = r & 0xFF
        report[46] = g & 0xFF
        report[47] = b & 0xFF

        return bytes(report)

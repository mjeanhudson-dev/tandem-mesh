"""
DualSense Kinematics, Trigger Filters, & Protocol Invariants.

Enforces the DualSense Gyro & Racing Architecture Rules directly in structure:
  Rule 1: Inverse pre-compensation for non-linear game distortions
          X_proxy = d_game + (1 - d_game) * sqrt(|x|) * sgn(x)
  Rule 2: Loading screen exit transition (200 ms C^2 Smootherstep blend)
          S(t) = 6t^5 - 15t^4 + 10t^3 (t in [0, 1])
  Rule 3: Menu trigger isolation & 15-count deadzone on L2/R2
          Swallows resting finger float (7-12 counts).
          Driving mode latched by R2 > 35 or rumble > 0.
  Rule 4: Lap & recline immunity (pitch between -15° and -75°)
          omega_roll = -(omega_z * cos(theta_pitch) + omega_y * sin(theta_pitch))
          Decouple lateral accelerometer (a_x) when |theta_pitch| > 30°.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple


class DualSenseKinematics:
    """
    Mathematical transformations for DualSense 6-axis gyro steering,
    loading screen stall recovery, and inverse non-linear compensation.
    """

    @staticmethod
    def smootherstep(t: float) -> float:
        """
        Calculates 200 ms C^2 Smootherstep blend:
          S(t) = 6t^5 - 15t^4 + 10t^3  (t in [0, 1])
        Continuously differentiable through second derivative to eliminate jerks.
        """
        t = max(0.0, min(1.0, float(t)))
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @classmethod
    def apply_transition_blend(
        cls,
        elapsed_sec: float,
        duration_sec: float = 0.2,
        current_value: float = 1.0,
    ) -> float:
        """
        Executes a 200 ms C^2 smootherstep blend on resume from scene transition or stall.
        Frame 0 softly zeroes (0.0), ramping smoothly to current_value at duration_sec.
        """
        if duration_sec <= 0.0:
            return current_value
        t = elapsed_sec / duration_sec
        return current_value * cls.smootherstep(t)

    @staticmethod
    def project_sagittal_steering(
        omega_z: float,
        omega_y: float,
        theta_pitch_deg: float,
        ax: float = 0.0,
    ) -> float:
        """
        Lap & Recline Immunity projection (Rule 4):
          omega_roll = -(omega_z * cos(theta_pitch) + omega_y * sin(theta_pitch))
        Natural driving postures recline between -15° and -75°.
        When reclined (|theta_pitch| > 30°), lateral accelerometer gravity (ax)
        is decoupled from the steering anchor to prevent steady corner decay.
        """
        theta_rad = math.radians(theta_pitch_deg)
        cos_p = math.cos(theta_rad)
        sin_p = math.sin(theta_rad)

        # Projected roll velocity across sagittal plane
        omega_roll = -(omega_z * cos_p + omega_y * sin_p)

        # Decouple lateral accelerometer gravity when reclined
        is_reclined = abs(theta_pitch_deg) > 30.0
        if not is_reclined and ax != 0.0:
            # When upright (|theta| <= 30°), slight anchor gravity blending is allowed
            omega_roll += ax * 0.05

        return omega_roll

    @staticmethod
    def inverse_precompensation(x: float, d_game: float = 0.15) -> float:
        """
        Non-linear game pre-compensation inverse curve (Rule 1):
          X_proxy = d_game + (1 - d_game) * sqrt(|x|) * sgn(x)
        Pre-compensates for deadzone swallows and quadratic game curves.
        """
        if x == 0.0:
            return 0.0
        sgn = 1.0 if x > 0 else -1.0
        abs_x = min(1.0, abs(x))
        return (d_game + (1.0 - d_game) * math.sqrt(abs_x)) * sgn


class DualSenseTriggerFilter:
    """
    Trigger filtering, deadzone enforcement, and driving latch logic.
    """

    @staticmethod
    def apply_menu_deadzone(raw_counts: int, deadzone: int = 15) -> int:
        """
        Enforce 15-count deadzone on L2 and R2 in frontend menus (Rule 3).
        Swallows resting finger float (typically 7-12 counts) to prevent
        unintended menu tab scrolling.
        """
        if raw_counts <= deadzone:
            return 0
        return min(255, raw_counts)

    @staticmethod
    def evaluate_driving_latch(
        r2_counts: int,
        game_rumble: int,
        currently_latched: bool = False,
    ) -> bool:
        """
        Driving mode (g_raceActive) latch rule:
        Only latched by active throttle (R2 > 35) or game rumble (> 0).
        Once latched, remains latched for the duration of the driving session.
        """
        if currently_latched:
            return True
        return (r2_counts > 35) or (game_rumble > 0)

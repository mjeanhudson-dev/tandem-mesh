"""
Tandem Core Type System & Structural Contracts.

Defines the mathematical, structural, and cryptographic invariants governing:
  1. Monotonic Information-Flow Taint Lattice (TaintLevel)
  2. Blast-Radius Scoring & Autonomy Gearbox (AutonomyGear, BlastRadius)
  3. Universal App-to-App (A2A) Capability Contracts (Capability, AppManifest)
  4. Universal App-to-Hand (A2H) Physical Device Envelopes (HandDevice, HapticProfile)
  5. Semantic Intent Dispatch (IntentRequest, IntentResponse)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import hashlib
import json
import time
from typing import Any, Callable, Optional


# ============================================================================
# 1. TAINT LATTICE & AUTONOMY GEARBOX ENUMS
# ============================================================================


class TaintLevel(IntEnum):
    """
    Monotonic information-flow taint lattice:
        UNTRUSTED_EXTERNAL (0) < QUARANTINED_DATA (1) < INTERNAL_AGENT (2)
        < PINPOINT_VERIFIED (3) < HUMAN_VERIFIED (4)
    """

    UNTRUSTED_EXTERNAL = 0
    QUARANTINED_DATA = 1
    INTERNAL_AGENT = 2
    PINPOINT_VERIFIED = 3
    HUMAN_VERIFIED = 4


class AutonomyGear(IntEnum):
    """
    5-Speed Human-in-the-Loop Autonomy Gearbox:
      G0_EBRAKE_STOP: Immediate atomic halt across all connected apps & agents.
      G1_CLUTCH_MANUAL: Full human confirmation on every action (blast ceiling: 0).
      G2_SPORT_TACTILE: Autonomous read/inspect (blast ceiling: 20). Local mutations prompt.
      G3_ARBITER_CRUISE: Verified local changes auto-approved (blast ceiling: 70).
      G4_AUTONOMOUS_MESH: Maximum autonomy for isolated simulation/mesh tasks (blast ceiling: 90).
    """

    G0_EBRAKE_STOP = 0
    G1_CLUTCH_MANUAL = 1
    G2_SPORT_TACTILE = 2
    G3_ARBITER_CRUISE = 3
    G4_AUTONOMOUS_MESH = 4

    @property
    def blast_ceiling(self) -> int:
        """Maximum blast radius allowed without physical hand ratification."""
        ceilings = {
            AutonomyGear.G0_EBRAKE_STOP: 0,
            AutonomyGear.G1_CLUTCH_MANUAL: 0,
            AutonomyGear.G2_SPORT_TACTILE: 20,
            AutonomyGear.G3_ARBITER_CRUISE: 70,
            AutonomyGear.G4_AUTONOMOUS_MESH: 90,
        }
        return ceilings[self]


# ============================================================================
# 2. STRUCTURAL EXCEPTIONS (Encode Lessons in Structure)
# ============================================================================


class TandemError(Exception):
    """Base exception for all Tandem mesh errors."""


class CapabilityNotFoundError(TandemError):
    """Raised when an intent targets an unregistered capability."""


class TaintAttenuationError(TandemError):
    """
    Raised when caller taint level is strictly lower than capability requirement.
    Structural protection: Prevents prompt injection & untrusted external data
    from triggering elevated internal or human-verified capabilities.
    """


class BlastRadiusRatificationRequired(TandemError):
    """
    Raised when an action's blast radius exceeds the active autonomy gear ceiling
    without explicit physical hand ratification (e.g. DualSense detent squeeze).
    Carries the synthesized HapticProfile so controllers can immediately engage detents.
    """

    def __init__(self, message: str, haptic_profile: Optional[HapticProfile] = None):
        super().__init__(message)
        self.haptic_profile = haptic_profile


class EBrakeTriggeredError(TandemError):
    """Raised when an intent is blocked due to an active E-Brake state."""


class SchemaValidationError(TandemError):
    """Raised when parameters fail capability type or schema validation."""


# ============================================================================
# 3. CAPABILITY & APP MANIFEST CONTRACTS (A2A)
# ============================================================================


@dataclass(frozen=True)
class CapabilityParameter:
    """Schema definition for a single capability argument."""

    name: str
    type_name: str  # 'string', 'int', 'float', 'bool', 'dict', 'list', 'any'
    description: str
    required: bool = True
    default: Any = None

    def validate(self, value: Any) -> Any:
        """Validate input value against declared type contract."""
        if value is None:
            if self.required:
                raise SchemaValidationError(f"Missing required parameter: '{self.name}'")
            return self.default

        type_map = {
            "string": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "dict": dict,
            "list": list,
            "any": object,
        }
        expected_type = type_map.get(self.type_name, object)
        # Note: in Python, bool is a subclass of int, so guard against True/False for int
        if self.type_name in ("int", "float") and isinstance(value, bool):
            raise SchemaValidationError(
                f"Parameter '{self.name}' expected {self.type_name}, got bool"
            )

        if not isinstance(value, expected_type):
            raise SchemaValidationError(
                f"Parameter '{self.name}' expected {self.type_name}, got {type(value).__name__}"
            )
        return value


@dataclass
class Capability:
    """A discrete executable capability exposed by an application to the mesh."""

    name: str
    description: str
    parameters: list[CapabilityParameter] = field(default_factory=list)
    min_taint_level: TaintLevel = TaintLevel.INTERNAL_AGENT
    blast_radius: int = 10  # 0 to 100
    handler: Optional[Callable[[dict[str, Any]], Any]] = None

    def validate_params(self, raw_params: Optional[dict[str, Any]]) -> dict[str, Any]:
        """Validate raw dictionary parameters against schema."""
        if raw_params is None:
            raw_params = {}
        elif not isinstance(raw_params, dict):
            raise SchemaValidationError(
                f"Expected dict for params in capability '{self.name}', got {type(raw_params).__name__}"
            )

        validated: dict[str, Any] = {}
        param_map = {p.name: p for p in self.parameters}

        # Check required & present
        for name, p in param_map.items():
            if name in raw_params:
                validated[name] = p.validate(raw_params[name])
            elif p.required:
                raise SchemaValidationError(f"Missing required parameter '{name}' for capability '{self.name}'")
            else:
                validated[name] = p.default

        # Include additional unconstrained params if any
        for k, v in raw_params.items():
            if k not in validated:
                validated[k] = v

        return validated


@dataclass
class AppManifest:
    """Semantic manifest of an application participating in the Tandem mesh."""

    app_id: str
    version: str
    description: str
    capabilities: list[Capability] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_capability(self, name: str) -> Optional[Capability]:
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None


# ============================================================================
# 4. APP-TO-HAND (A2H) PHYSICAL DEVICE CONTRACTS
# ============================================================================


@dataclass
class HandDevice:
    """Physical human-in-the-loop controller, tactile switch, or mobile gateway."""

    device_id: str
    device_type: str  # 'dualsense', 'mobile_button', 'slider', 'foot_pedal', 'keyboard'
    active_gear: AutonomyGear = AutonomyGear.G2_SPORT_TACTILE
    haptic_capable: bool = True
    last_ratification_timestamp: float = 0.0
    is_ebrake_active: bool = False
    is_driving_latched: bool = False

    def ratify(self) -> None:
        """Mark physical operator ratification of elevated blast-radius."""
        self.last_ratification_timestamp = time.time()

    def consume_ratification(self) -> None:
        """Consume fresh ratification to enforce single-use protection."""
        self.last_ratification_timestamp = 0.0

    def is_ratification_fresh(self, ttl_seconds: float = 5.0) -> bool:
        """True if the operator ratified within the valid time-to-live window."""
        if self.last_ratification_timestamp <= 0.0:
            return False
        return (time.time() - self.last_ratification_timestamp) <= ttl_seconds

    def evaluate_trigger(
        self,
        trigger_counts: int,
        is_menu: bool = False,
        detent_threshold: int = 128,
        game_rumble: int = 0,
    ) -> bool:
        """
        Evaluate physical trigger input (0-255 counts).
        Enforces Rule 3 (15-count deadzone in menus to eliminate resting finger float).
        Latches driving mode if R2 > 35 or game_rumble > 0.
        Returns True and triggers ratify() if squeezed past detent_threshold.
        """
        if is_menu and trigger_counts <= 15:
            # Swallow resting finger float (7-12 counts) per Rule 3
            return False

        if trigger_counts > 35 or game_rumble > 0:
            self.is_driving_latched = True

        if trigger_counts >= detent_threshold:
            self.ratify()
            return True
        return False


@dataclass(frozen=True)
class HapticProfile:
    """
    Physical tactile resistance and visual telemetry package.
    Synthesized directly from action blast radius B(a) in [0, 100].
    """

    blast_radius: int
    lightbar_rgb: tuple[int, int, int]
    left_trigger_mode: int
    left_trigger_params: bytes
    right_trigger_mode: int
    right_trigger_params: bytes
    motor_rumble_left: int
    motor_rumble_right: int
    mobile_vibration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "blast_radius": self.blast_radius,
            "lightbar_rgb": list(self.lightbar_rgb),
            "left_trigger_mode": self.left_trigger_mode,
            "left_trigger_params": list(self.left_trigger_params),
            "right_trigger_mode": self.right_trigger_mode,
            "right_trigger_params": list(self.right_trigger_params),
            "motor_rumble_left": self.motor_rumble_left,
            "motor_rumble_right": self.motor_rumble_right,
            "mobile_vibration_ms": self.mobile_vibration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HapticProfile:
        left_params = bytes(data.get("left_trigger_params", []))
        right_params = bytes(data.get("right_trigger_params", []))
        if len(left_params) < 7:
            left_params = left_params + bytes(7 - len(left_params))
        if len(right_params) < 7:
            right_params = right_params + bytes(7 - len(right_params))

        left_mode = data.get("left_trigger_mode", 0)
        if isinstance(left_mode, str):
            left_mode = int(left_mode, 16) if left_mode.startswith("0x") else int(left_mode)

        right_mode = data.get("right_trigger_mode", 0)
        if isinstance(right_mode, str):
            right_mode = int(right_mode, 16) if right_mode.startswith("0x") else int(right_mode)

        rgb = data.get("lightbar_rgb", (0, 200, 255))
        if isinstance(rgb, list):
            rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

        return cls(
            blast_radius=int(data.get("blast_radius", 0)),
            lightbar_rgb=rgb,
            left_trigger_mode=int(left_mode),
            left_trigger_params=left_params,
            right_trigger_mode=int(right_mode),
            right_trigger_params=right_params,
            motor_rumble_left=int(data.get("motor_rumble_left", 0)),
            motor_rumble_right=int(data.get("motor_rumble_right", 0)),
            mobile_vibration_ms=int(data.get("mobile_vibration_ms", 0)),
        )


# ============================================================================
# 5. INTENT ENVELOPES (L7 APPLICATION PROTOCOL)
# ============================================================================


@dataclass
class IntentRequest:
    """Structural envelope for dispatching an intent across the Tandem mesh."""

    request_id: str
    target_capability: str
    params: dict[str, Any]
    caller_app_id: str
    caller_taint: TaintLevel = TaintLevel.INTERNAL_AGENT
    timestamp_sec: float = field(default_factory=time.time)
    ratified_by_hand: bool = False
    trace_id: Optional[str] = None


@dataclass
class IntentResponse:
    """Result envelope emitted by the mesh after executing an intent."""

    request_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    taint_level: TaintLevel = TaintLevel.INTERNAL_AGENT
    execution_time_ms: float = 0.0
    haptic_telemetry: Optional[HapticProfile] = None

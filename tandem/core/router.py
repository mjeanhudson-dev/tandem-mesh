"""
Semantic Intent Router & Execution Engine.

Glues A2A capability dispatch and A2H physical agency checks into an atomic,
structurally-enforced pipeline.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable, Optional

from tandem.core.haptics import HapticSynthesizer
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.registry import CapabilityRegistry
from tandem.core.types import (
    AutonomyGear,
    BlastRadiusRatificationRequired,
    Capability,
    EBrakeTriggeredError,
    HandDevice,
    IntentRequest,
    IntentResponse,
    TaintLevel,
)


class IntentRouter:
    """
    Central dispatch and validation router for the Tandem mesh.
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        lattice: Optional[StructuralTaintLattice] = None,
    ) -> None:
        self.registry = registry or CapabilityRegistry()
        self.lattice = lattice or StructuralTaintLattice()
        self._ebrake_active = False
        self._ebrake_callbacks: list[Callable[[], None]] = []
        self._hand_devices: dict[str, HandDevice] = {}

    def register_hand(self, device: HandDevice) -> None:
        """Bind a physical hand device to the router."""
        self._hand_devices[device.device_id] = device

    def unregister_hand(self, device_id: str) -> None:
        """Unbind a physical hand device."""
        self._hand_devices.pop(device_id, None)

    def get_primary_hand(self) -> Optional[HandDevice]:
        """Return the primary active hand device, if any."""
        if not self._hand_devices:
            return None
        return next(iter(self._hand_devices.values()))

    def press_ebrake(self, source: str = "operator") -> None:
        """
        Engage emergency brake across the entire mesh.
        Immediately stops all pending and incoming intents.
        """
        self._ebrake_active = True
        for dev in self._hand_devices.values():
            dev.is_ebrake_active = True
            dev.active_gear = AutonomyGear.G0_EBRAKE_STOP

        for cb in self._ebrake_callbacks:
            try:
                cb()
            except Exception:
                pass

    def release_ebrake(self) -> None:
        """Release the emergency brake and return to G2_SPORT_TACTILE."""
        self._ebrake_active = False
        for dev in self._hand_devices.values():
            dev.is_ebrake_active = False
            dev.active_gear = AutonomyGear.G2_SPORT_TACTILE

    def on_ebrake(self, callback: Callable[[], None]) -> None:
        """Register a callback to run immediately upon E-Brake engagement."""
        self._ebrake_callbacks.append(callback)

    def dispatch(self, request: IntentRequest) -> IntentResponse:
        """
        Execute an intent request through the full structural validation pipeline:
          1. E-Brake validation
          2. Capability resolution
          3. Taint lattice verification
          4. Blast-radius & physical hand ratification
          5. Parameter schema validation
          6. Handler execution
          7. Haptic profile synthesis
        """
        start_time = time.perf_counter()

        # 1. Check E-Brake
        if self._ebrake_active:
            raise EBrakeTriggeredError(
                "Intent rejected: Emergency E-Brake is actively engaged across the mesh."
            )

        # 2. Resolve capability
        cap = self.registry.get_capability(request.target_capability)

        # 3. Taint lattice check (structural protection against untrusted prompt injection)
        self.lattice.verify_dispatch_allowed(
            caller_taint=request.caller_taint,
            min_required_taint=cap.min_taint_level,
            capability_name=cap.name,
        )

        # 4. Blast-radius and Hand Ratification check
        primary_hand = self.get_primary_hand()
        current_gear = (
            primary_hand.active_gear
            if primary_hand is not None
            else AutonomyGear.G2_SPORT_TACTILE
        )

        if cap.blast_radius > current_gear.blast_ceiling:
            # Requires ratification from hand
            is_ratified = request.ratified_by_hand or (
                primary_hand is not None and primary_hand.is_ratification_fresh()
            )
            if not is_ratified:
                haptics = HapticSynthesizer.synthesize(
                    blast_radius=cap.blast_radius,
                    active_gear=current_gear,
                    ebrake_active=self._ebrake_active,
                )
                raise BlastRadiusRatificationRequired(
                    f"Action '{cap.name}' has blast radius {cap.blast_radius}, exceeding "
                    f"autonomy gear {current_gear.name} ceiling ({current_gear.blast_ceiling}). "
                    f"Tactile detent squeeze or explicit ratification required.",
                    haptic_profile=haptics,
                )
            elif primary_hand is not None and not request.ratified_by_hand:
                # Consume fresh hand ratification to prevent multi-action replay
                primary_hand.consume_ratification()

        # 5. Validate parameters against capability schema
        validated_params = cap.validate_params(request.params)

        # 6. Execute handler
        try:
            if cap.handler is None:
                result_data = {
                    "status": "acknowledged",
                    "capability": cap.name,
                    "params": validated_params,
                }
            else:
                result_data = cap.handler(validated_params)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # 7. Synthesize haptic telemetry
            haptics = HapticSynthesizer.synthesize(
                blast_radius=cap.blast_radius,
                active_gear=current_gear,
                ebrake_active=self._ebrake_active,
            )

            return IntentResponse(
                request_id=request.request_id,
                success=True,
                data=result_data,
                taint_level=cap.min_taint_level,
                execution_time_ms=elapsed_ms,
                haptic_telemetry=haptics,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                taint_level=request.caller_taint,
                execution_time_ms=elapsed_ms,
            )

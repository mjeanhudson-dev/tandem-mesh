"""
Tandem Deep Module Facade.

Per /codebase-design:
  "Design deep modules: a lot of behaviour behind a small interface, placed at a clean seam,
   testable through that interface. The aim is leverage for callers, locality for maintainers,
   and testability for everyone."

The Tandem client provides an ultra-ergonomic API for any app, harness, or physical device.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from typing import Any, Callable, Optional

from tandem.core.haptics import HapticSynthesizer
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.registry import CapabilityRegistry
from tandem.core.router import IntentRouter
from tandem.core.types import (
    AppManifest,
    AutonomyGear,
    Capability,
    CapabilityParameter,
    HandDevice,
    HapticProfile,
    IntentRequest,
    IntentResponse,
    TaintLevel,
)
from tandem.harness.adapter import HarnessMeshAdapter
from tandem.transport.base import TransportAdapter
from tandem.transport.memory import MemoryTransport


class Tandem:
    """
    Unified entry point for the Tandem App-to-App & App-to-Hand Coordination Mesh.
    """

    def __init__(
        self,
        transport: Optional[TransportAdapter] = None,
        router: Optional[IntentRouter] = None,
        app_id: str = "tandem_app",
    ) -> None:
        self.app_id = app_id
        self.router = router or IntentRouter()
        self.transport = transport or MemoryTransport()
        self.transport.set_handler(self.router.dispatch)
        self.transport.start()
        self._harness_adapter = HarnessMeshAdapter(self.router, agent_id=self.app_id)

    @classmethod
    def local(cls, app_id: str = "local_node") -> Tandem:
        """Create an in-memory local node (ideal for local testing and agent harnesses)."""
        return cls(transport=MemoryTransport(), app_id=app_id)

    @classmethod
    def connect(cls, transport: TransportAdapter, app_id: str = "remote_node") -> Tandem:
        """Connect to an external transport seam (e.g. Tailscale HTTP or IPC pipe)."""
        return cls(transport=transport, app_id=app_id)

    def close(self) -> None:
        """Tear down transport and release mesh resources."""
        self.transport.stop()

    def register_app(self, manifest: AppManifest) -> None:
        """Register an application and all its capabilities in the mesh."""
        self.router.registry.register_app(manifest)

    def register_capability(
        self,
        name: str,
        description: str,
        handler: Optional[Callable[[dict[str, Any]], Any]] = None,
        parameters: Optional[list[CapabilityParameter]] = None,
        blast_radius: int = 10,
        min_taint_level: TaintLevel = TaintLevel.INTERNAL_AGENT,
    ) -> None:
        """Ergonomic shorthand to register a single capability directly."""
        cap = Capability(
            name=name,
            description=description,
            parameters=parameters or [],
            min_taint_level=min_taint_level,
            blast_radius=blast_radius,
            handler=handler,
        )
        existing = self.router.registry.get_app(self.app_id)
        if existing:
            updated_caps = [c for c in existing.capabilities if c.name != cap.name]
            updated_caps.append(cap)
            existing.capabilities = updated_caps
            self.router.registry.register_app(existing)
        else:
            manifest = AppManifest(
                app_id=self.app_id,
                version="1.0.0",
                description=f"Auto-generated manifest for {self.app_id}",
                capabilities=[cap],
            )
            self.register_app(manifest)

    def register_hand(
        self,
        device_id: str = "hand_primary",
        device_type: str = "dualsense",
        active_gear: AutonomyGear = AutonomyGear.G2_SPORT_TACTILE,
    ) -> HandDevice:
        """Bind a physical hand device (DualSense, mobile button, slider) to this session."""
        device = HandDevice(
            device_id=device_id,
            device_type=device_type,
            active_gear=active_gear,
        )
        self.router.register_hand(device)
        return device

    def call(
        self,
        capability_name: str,
        params: Optional[dict[str, Any]] = None,
        caller_taint: TaintLevel = TaintLevel.INTERNAL_AGENT,
        ratified_by_hand: bool = False,
    ) -> IntentResponse:
        """
        Ultra-ergonomic dispatch: executes target capability across the mesh
        with structural taint checking, blast-radius detents, and haptic synthesis.
        """
        req = IntentRequest(
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            target_capability=capability_name,
            params=params or {},
            caller_app_id=self.app_id,
            caller_taint=caller_taint,
            ratified_by_hand=ratified_by_hand,
        )
        return self.transport.send(req)

    def press_ebrake(self) -> None:
        """Trigger emergency stop across the mesh and all connected transports."""
        self.router.press_ebrake(source=self.app_id)
        self.transport.broadcast_ebrake()

    def release_ebrake(self) -> None:
        """Release emergency stop and return to standard operation."""
        self.router.release_ebrake()
        self.transport.release_ebrake()

    def on_ebrake(self, callback: Callable[[], None]) -> None:
        """Register callback invoked when E-Brake is engaged."""
        self.router.on_ebrake(callback)

    def synthesize_haptics(self, blast_radius: int) -> HapticProfile:
        """Synthesize tactile resistance and lightbar profile for given risk metric."""
        primary_hand = self.router.get_primary_hand()
        gear = primary_hand.active_gear if primary_hand else AutonomyGear.G2_SPORT_TACTILE
        return HapticSynthesizer.synthesize(blast_radius=blast_radius, active_gear=gear)

    def as_mcp_tools(self) -> list[dict[str, Any]]:
        """Export all mesh capabilities as standardized MCP / LLM tools."""
        return self._harness_adapter.get_tool_definitions()

    def execute_harness_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call emitted by an LLM harness."""
        return self._harness_adapter.execute_tool(tool_name, arguments)


def main() -> None:
    """CLI diagnostics and interactive runner for Tandem mesh."""
    parser = argparse.ArgumentParser(
        description="Tandem: Universal App-to-App & App-to-Hand Mesh CLI"
    )
    parser.add_argument("--catalog", action="store_true", help="Dump mesh capability catalog")
    parser.add_argument("--test-haptic", type=int, help="Synthesize and inspect haptic profile for blast radius [0-100]")
    parser.add_argument("--ebrake", action="store_true", help="Engage emergency brake")
    args = parser.parse_args()

    node = Tandem.local(app_id="cli_diagnostic")

    if args.test_haptic is not None:
        profile = node.synthesize_haptics(args.test_haptic)
        print(f"Haptic Profile for Blast Radius {args.test_haptic}:")
        print(json.dumps(profile.to_dict(), indent=2))
        hid = HapticSynthesizer.generate_dualsense_hid_report(profile)
        print(f"DualSense USB HID Report (64 bytes): {hid[:16].hex()}... (length: {len(hid)})")
    elif args.ebrake:
        node.press_ebrake()
        print("Engaged Emergency E-Brake across mesh.")
    else:
        print("Tandem Mesh initialized. Available tools:")
        print(json.dumps(node.as_mcp_tools(), indent=2))


if __name__ == "__main__":
    main()

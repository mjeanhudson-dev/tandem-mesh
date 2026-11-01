"""
Tandem: Universal App-to-App (A2A) & App-to-Hand (A2H) Orchestration Mesh.

Bridging heterogeneous applications, agent harnesses, and physical human-in-the-loop
tactile devices (DualSense, mobile switches, haptic detents) over universal protocols.
"""

from tandem.client import Tandem
from tandem.core.types import (
    AppManifest,
    AutonomyGear,
    BlastRadiusRatificationRequired,
    Capability,
    CapabilityNotFoundError,
    CapabilityParameter,
    EBrakeTriggeredError,
    HandDevice,
    HapticProfile,
    IntentRequest,
    IntentResponse,
    SchemaValidationError,
    TaintAttenuationError,
    TaintLevel,
    TandemError,
)
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.registry import CapabilityRegistry
from tandem.core.haptics import HapticSynthesizer
from tandem.core.router import IntentRouter
from tandem.core.dualsense import DualSenseKinematics, DualSenseTriggerFilter
from tandem.transport.base import TransportAdapter
from tandem.transport.memory import MemoryTransport
from tandem.transport.pipe import PipeTransport
from tandem.transport.tailscale_http import TailscaleHttpTransport
from tandem.harness.adapter import HarnessMeshAdapter
from tandem.harness.mcp_server import TandemMcpServer

__all__ = [
    "Tandem",
    "AppManifest",
    "AutonomyGear",
    "BlastRadiusRatificationRequired",
    "Capability",
    "CapabilityNotFoundError",
    "CapabilityParameter",
    "EBrakeTriggeredError",
    "HandDevice",
    "HapticProfile",
    "IntentRequest",
    "IntentResponse",
    "SchemaValidationError",
    "TaintAttenuationError",
    "TaintLevel",
    "TandemError",
    "StructuralTaintLattice",
    "CapabilityRegistry",
    "HapticSynthesizer",
    "IntentRouter",
    "DualSenseKinematics",
    "DualSenseTriggerFilter",
    "TransportAdapter",
    "MemoryTransport",
    "PipeTransport",
    "TailscaleHttpTransport",
    "HarnessMeshAdapter",
    "TandemMcpServer",
]

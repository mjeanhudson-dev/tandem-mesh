"""
Tier 3 Cross-Feature Interaction: A2H Detents + Ratification + Single-Use Consumption.
Verifies pairwise interaction between:
- Blast-radius risk gating
- Physical hand device trigger detent evaluation
- Sliding TTL window and single-use token consumption
- DualSense haptic profile resistance synthesis
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

from tandem.core.types import (
    AppManifest, Capability, CapabilityParameter, IntentRequest, IntentResponse,
    TaintLevel, AutonomyGear, HandDevice, BlastRadiusRatificationRequired
)
from tandem.core.registry import CapabilityRegistry
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.router import IntentRouter
from tandem.transport.memory import MemoryTransport


class TestA2HDetentAndRatification(unittest.TestCase):

    def setUp(self):
        self.registry = CapabilityRegistry()
        self.lattice = StructuralTaintLattice()
        self.router = IntentRouter(self.registry, self.lattice)
        self.transport = MemoryTransport()
        self.transport.set_handler(self.router.dispatch)
        self.router.on_ebrake(self.transport.broadcast_ebrake)
        self.transport.start()

        # Register DualSense hand device in G2_SPORT_TACTILE (blast ceiling: 20)
        self.hand = HandDevice(
            device_id="dualsense_primary",
            device_type="dualsense",
            active_gear=AutonomyGear.G2_SPORT_TACTILE
        )
        self.router.register_hand(self.hand)

        # High blast-radius capability (blast_radius: 50 > 20)
        cap_format = Capability(
            name="storage.format_partition",
            description="Formats secondary storage disk",
            parameters=[CapabilityParameter(name="drive", type_name="string", description="Drive letter")],
            handler=lambda p: {"status": "formatted", "drive": p["drive"]},
            blast_radius=50,
            min_taint_level=TaintLevel.INTERNAL_AGENT
        )
        self.registry.register_app(AppManifest(
            app_id="storage_manager",
            version="1.0.0",
            description="Storage Administration",
            capabilities=[cap_format]
        ))

    def tearDown(self):
        self.transport.stop()

    def test_i1_unratified_high_blast_action_demands_ratification_and_haptic_profile(self):
        """Interaction 1: Dispatch exceeding blast ceiling fails with BlastRadiusRatificationRequired."""
        req = IntentRequest(
            request_id="req-format-1",
            target_capability="storage.format_partition",
            params={"drive": "D:"},
            caller_app_id="agent_harness",
            caller_taint=TaintLevel.INTERNAL_AGENT
        )
        with self.assertRaises(BlastRadiusRatificationRequired) as ctx:
            self.transport.send(req)

        # Verify synthesized haptic profile returned with exception
        ex = ctx.exception
        self.assertIsNotNone(ex.haptic_profile)
        self.assertEqual(ex.haptic_profile.blast_radius, 50)
        # Moderate risk produces Amber lightbar (255, 140, 0) and trigger resistance
        self.assertEqual(ex.haptic_profile.lightbar_rgb, (255, 140, 0))

    def test_i2_ratification_squeeze_allows_execution_and_consumes_token(self):
        """Interaction 2: Operator trigger squeeze past detent allows execution and immediately consumes token."""
        # 1. Operator pulls DualSense right trigger to count 140 (past 128 detent)
        ratified = self.hand.evaluate_trigger(trigger_counts=140, is_menu=False)
        self.assertTrue(ratified)
        self.assertTrue(self.hand.is_ratification_fresh())

        # 2. Re-dispatch intent with fresh ratification
        req = IntentRequest(
            request_id="req-format-2",
            target_capability="storage.format_partition",
            params={"drive": "D:"},
            caller_app_id="agent_harness",
            caller_taint=TaintLevel.INTERNAL_AGENT
        )
        resp = self.transport.send(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["status"], "formatted")

        # 3. Ratification token MUST be consumed immediately
        self.assertFalse(self.hand.is_ratification_fresh(), "Token must be single-use consumed")

        # 4. Immediate duplicate call without re-squeezing must be blocked
        req_duplicate = IntentRequest(
            request_id="req-format-3",
            target_capability="storage.format_partition",
            params={"drive": "E:"},
            caller_app_id="agent_harness",
            caller_taint=TaintLevel.INTERNAL_AGENT
        )
        with self.assertRaises(BlastRadiusRatificationRequired):
            self.transport.send(req_duplicate)


if __name__ == "__main__":
    unittest.main()

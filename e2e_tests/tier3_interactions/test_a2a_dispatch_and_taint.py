"""
Tier 3 Cross-Feature Interaction: A2A Intent Dispatch + Monotonic Taint Propagation.
Verifies pairwise interaction between Capability Dispatch and the Monotonic Information-Flow Lattice:
- Caller taint boundary enforcement
- Monotonic output taint attenuation
- Network transport taint clamping (TailscaleHttpTransport) preventing remote privilege escalation
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
    TaintLevel, TaintAttenuationError
)
from tandem.core.registry import CapabilityRegistry
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.router import IntentRouter
from tandem.transport.memory import MemoryTransport
from tandem.transport.tailscale_http import TailscaleHttpTransport


class TestA2ADispatchAndTaint(unittest.TestCase):

    def setUp(self):
        self.registry = CapabilityRegistry()
        self.lattice = StructuralTaintLattice()
        self.router = IntentRouter(self.registry, self.lattice)
        self.transport = MemoryTransport()
        self.transport.set_handler(self.router.dispatch)
        self.router.on_ebrake(self.transport.broadcast_ebrake)
        self.transport.start()

        # Register privileged deployment capability
        cap_deploy = Capability(
            name="cloud.deploy_service",
            description="Deploys production cloud container",
            parameters=[CapabilityParameter(name="image", type_name="string", description="Container image")],
            handler=lambda p: {"status": "deployed", "image": p["image"]},
            blast_radius=10,
            min_taint_level=TaintLevel.INTERNAL_AGENT
        )
        # Register unprivileged public read capability
        cap_read = Capability(
            name="public.get_metrics",
            description="Returns system metrics",
            parameters=[],
            handler=lambda p: {"metrics": [1, 2, 3]},
            blast_radius=0,
            min_taint_level=TaintLevel.UNTRUSTED_EXTERNAL
        )
        self.registry.register_app(AppManifest(
            app_id="cloud_ops",
            version="1.0.0",
            description="Cloud Ops Application",
            capabilities=[cap_deploy, cap_read]
        ))

    def tearDown(self):
        self.transport.stop()

    def test_i1_untrusted_caller_blocked_from_privileged_capability(self):
        """Interaction 1: Untrusted caller attempting privileged dispatch is rejected with TaintAttenuationError."""
        req = IntentRequest(
            request_id="req-untrusted-1",
            target_capability="cloud.deploy_service",
            params={"image": "evil_image:latest"},
            caller_app_id="external_webhook",
            caller_taint=TaintLevel.UNTRUSTED_EXTERNAL
        )
        with self.assertRaises(TaintAttenuationError):
            self.transport.send(req)

    def test_i2_trusted_caller_executes_and_preserves_internal_agent_taint(self):
        """Interaction 2: Trusted caller invokes capability and receives proper response taint level."""
        req = IntentRequest(
            request_id="req-trusted-1",
            target_capability="cloud.deploy_service",
            params={"image": "app:v1.0.0"},
            caller_app_id="internal_ci_agent",
            caller_taint=TaintLevel.INTERNAL_AGENT
        )
        resp = self.transport.send(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["status"], "deployed")
        self.assertEqual(resp.taint_level, TaintLevel.INTERNAL_AGENT)

    def test_i3_tailscale_http_transport_inbound_taint_clamping(self):
        """Interaction 3: Inbound payload over network transport claiming INTERNAL_AGENT is clamped to UNTRUSTED."""
        http_transport = TailscaleHttpTransport(peer_url="http://127.0.0.1:8855")
        # Verify clamp_inbound_taint logic
        clamped_taint = http_transport.clamp_inbound_taint(claimed_taint_name="HUMAN_VERIFIED")
        self.assertEqual(clamped_taint, TaintLevel.UNTRUSTED_EXTERNAL)

        # Dispatched with clamped taint to privileged capability must be rejected
        req_remote = IntentRequest(
            request_id="req-remote-spoofed",
            target_capability="cloud.deploy_service",
            params={"image": "spoofed:latest"},
            caller_app_id="remote_node",
            caller_taint=clamped_taint
        )
        with self.assertRaises(TaintAttenuationError):
            self.transport.send(req_remote)


if __name__ == "__main__":
    unittest.main()

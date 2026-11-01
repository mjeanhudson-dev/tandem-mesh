"""
Tier 3 Cross-Feature Interaction: Multithreaded PipeTransport + Atomic E-Brake Halt.
Verifies pairwise interaction between:
- Multithreaded PipeTransport worker queues
- Router E-Brake engagement broadcasting across threads
- Instant rejection of pending requests with EBrakeTriggeredError
- Zero queue poisoning or deadlocks upon E-Brake release
"""

import sys
import threading
import time
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
    TaintLevel, EBrakeTriggeredError
)
from tandem.core.registry import CapabilityRegistry
from tandem.core.lattice import StructuralTaintLattice
from tandem.core.router import IntentRouter
from tandem.transport.pipe import PipeTransport


class TestEBrakeMultithreadPipe(unittest.TestCase):

    def setUp(self):
        self.registry = CapabilityRegistry()
        self.lattice = StructuralTaintLattice()
        self.router = IntentRouter(self.registry, self.lattice)

        # Register processing capability with slight delay to exercise queue
        cap_compute = Capability(
            name="sim.heavy_calc",
            description="Simulates numerical calculation",
            parameters=[CapabilityParameter(name="val", type_name="int", description="Input value")],
            handler=lambda p: {"result": p["val"] * 2},
            blast_radius=5,
            min_taint_level=TaintLevel.UNTRUSTED_EXTERNAL
        )
        self.registry.register_app(AppManifest(
            app_id="simulation_worker",
            version="1.0.0",
            description="Simulation Engine",
            capabilities=[cap_compute]
        ))

        self.pipe = PipeTransport(timeout_sec=2.0)
        self.pipe.set_handler(self.router.dispatch)
        self.router.on_ebrake(self.pipe.broadcast_ebrake)
        self.pipe.start()

    def tearDown(self):
        self.pipe.stop()

    def test_i1_concurrent_pipe_dispatch_halted_by_ebrake_and_resumed_cleanly(self):
        """Interaction: Concurrent requests dispatched through pipe are halted by E-Brake and recover on release."""
        # 1. Warm-up normal request passes
        req_init = IntentRequest(
            request_id="req-init",
            target_capability="sim.heavy_calc",
            params={"val": 21},
            caller_app_id="tester"
        )
        resp_init = self.pipe.send(req_init)
        self.assertTrue(resp_init.success)
        self.assertEqual(resp_init.data["result"], 42)

        # 2. Engage E-Brake
        self.router.press_ebrake(source="safety_controller")
        self.assertTrue(self.router._ebrake_active)

        # 3. Dispatches from multiple threads must fail with EBrakeTriggeredError
        thread_errors = []
        def worker_attempt(req_id: str):
            try:
                r = IntentRequest(
                    request_id=req_id,
                    target_capability="sim.heavy_calc",
                    params={"val": 10},
                    caller_app_id="thread_worker"
                )
                self.pipe.send(r)
            except EBrakeTriggeredError as e:
                thread_errors.append(type(e).__name__)
            except Exception as e:
                thread_errors.append(f"Unexpected: {type(e).__name__}")

        threads = [
            threading.Thread(target=worker_attempt, args=(f"req_blocked_{i}",))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(thread_errors), 5)
        self.assertTrue(all(err == "EBrakeTriggeredError" for err in thread_errors))

        # 4. Release E-Brake and confirm pipe recovers with zero poisoned queue entries
        self.router.release_ebrake()
        self.pipe.release_ebrake()
        self.assertFalse(self.router._ebrake_active)

        # 5. Subsequent dispatches must succeed immediately
        req_resumed = IntentRequest(
            request_id="req-resumed",
            target_capability="sim.heavy_calc",
            params={"val": 50},
            caller_app_id="tester"
        )
        resp_resumed = self.pipe.send(req_resumed)
        self.assertTrue(resp_resumed.success)
        self.assertEqual(resp_resumed.data["result"], 100)


if __name__ == "__main__":
    unittest.main()

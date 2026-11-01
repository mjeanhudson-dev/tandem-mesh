"""
Unit tests for Tandem Transport Adapters (Memory, Pipe, and Tailscale HTTP).
"""

from __future__ import annotations

import json
import unittest

from tandem.core.router import IntentRouter
from tandem.core.types import (
    Capability,
    CapabilityParameter,
    EBrakeTriggeredError,
    IntentRequest,
    IntentResponse,
    TaintLevel,
)
from tandem.transport.memory import MemoryTransport
from tandem.transport.pipe import PipeTransport
from tandem.transport.tailscale_http import TailscaleHttpTransport


class TestTransports(unittest.TestCase):
    def setUp(self) -> None:
        self.router = IntentRouter()
        self.router.registry.register_app(
            # Simple test app
            type(
                "AppStub",
                (),
                {
                    "app_id": "test_app",
                    "version": "1.0",
                    "description": "Test App",
                    "capabilities": [
                        Capability(
                            name="echo",
                            description="Echo input text",
                            parameters=[
                                CapabilityParameter(name="msg", type_name="string", description="Text")
                            ],
                            blast_radius=5,
                            handler=lambda p: {"echo": p["msg"]},
                        ),
                        Capability(
                            name="admin_drop",
                            description="Privileged admin operation",
                            min_taint_level=TaintLevel.INTERNAL_AGENT,
                            blast_radius=80,
                            handler=lambda p: {"status": "dropped"},
                        ),
                    ],
                    "get_capability": lambda self, name: next(
                        (c for c in self.capabilities if c.name == name), None
                    ),
                },
            )()
        )

    def test_memory_transport_lifecycle_and_send(self) -> None:
        transport = MemoryTransport()
        transport.set_handler(self.router.dispatch)

        # Before start
        req = IntentRequest(
            request_id="req_mem_1",
            target_capability="echo",
            params={"msg": "hello memory"},
            caller_app_id="caller_1",
        )
        resp_unstarted = transport.send(req)
        self.assertFalse(resp_unstarted.success)
        self.assertIn("TransportNotStartedError", resp_unstarted.error)

        # Start
        transport.start()
        resp = transport.send(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["echo"], "hello memory")

        # E-Brake engagement
        transport.broadcast_ebrake()
        with self.assertRaises(EBrakeTriggeredError):
            transport.send(req)

        # Release E-Brake resumes transmission
        transport.release_ebrake()
        resp_resumed = transport.send(req)
        self.assertTrue(resp_resumed.success)

        transport.stop()

    def test_pipe_transport_queue_processing(self) -> None:
        import threading
        import time

        pipe = PipeTransport(timeout_sec=2.0)
        pipe.set_handler(self.router.dispatch)
        pipe.start()

        req = IntentRequest(
            request_id="req_pipe_1",
            target_capability="echo",
            params={"msg": "hello pipe"},
            caller_app_id="caller_pipe",
        )
        resp = pipe.send(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["echo"], "hello pipe")

        # Concurrency test: Multiple threads calling send concurrently
        results: dict[str, str] = {}
        def worker(req_id: str, msg: str) -> None:
            r = IntentRequest(
                request_id=req_id,
                target_capability="echo",
                params={"msg": msg},
                caller_app_id="concurrent_caller",
            )
            res = pipe.send(r)
            results[req_id] = res.data["echo"]

        threads = [
            threading.Thread(target=worker, args=(f"req_t_{i}", f"msg_{i}"))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i in range(5):
            self.assertEqual(results[f"req_t_{i}"], f"msg_{i}")

        # E-Brake test on pipe
        pipe.broadcast_ebrake()
        with self.assertRaises(EBrakeTriggeredError):
            pipe.send(req)

        pipe.release_ebrake()
        resp_after_ebrake = pipe.send(req)
        self.assertTrue(resp_after_ebrake.success)

        pipe.stop()

    def test_pipe_transport_timeout_does_not_poison_subsequent_requests(self) -> None:
        import time

        pipe = PipeTransport(timeout_sec=0.05)
        # Handler delays for 0.15s, exceeding the 0.05s timeout
        pipe.set_handler(
            lambda r: (time.sleep(0.15), IntentResponse(request_id=r.request_id, success=True, data=r.request_id))[1]
        )
        pipe.start()

        # Request 1 times out
        req1 = IntentRequest(request_id="req_1", target_capability="echo", params={}, caller_app_id="app")
        resp1 = pipe.send(req1)
        self.assertFalse(resp1.success)
        self.assertIn("TimeoutError", resp1.error)

        # Wait for worker to finish processing request 1
        time.sleep(0.2)

        # Now replace with fast handler for request 2 and restore healthy timeout
        pipe.set_handler(lambda r: IntentResponse(request_id=r.request_id, success=True, data=r.request_id))
        pipe.timeout_sec = 2.0

        # Request 2 must NOT receive request 1's late response
        req2 = IntentRequest(request_id="req_2", target_capability="echo", params={}, caller_app_id="app")
        resp2 = pipe.send(req2)
        self.assertTrue(resp2.success, f"resp2 failed: {resp2.error}, request_id={resp2.request_id}")
        self.assertEqual(resp2.request_id, "req_2")
        self.assertEqual(resp2.data, "req_2")

        pipe.stop()

    def test_tailscale_http_inbound_taint_clamping(self) -> None:
        """
        Structural Test: When receiving an inbound JSON payload over Tailscale/network:
        If authenticated=False, taint MUST be clamped to UNTRUSTED_EXTERNAL.
        This ensures an external network actor cannot invoke an INTERNAL_AGENT capability.
        """
        ts_transport = TailscaleHttpTransport(
            peer_url="http://100.64.0.50:8855",
            auth_token="secret_token",
        )
        ts_transport.set_handler(self.router.dispatch)
        ts_transport.start()

        # 1. Unauthenticated inbound request targeting admin_drop (requires INTERNAL_AGENT)
        raw_unauth_json = json.dumps(
            {
                "request_id": "req_net_unauth",
                "target_capability": "admin_drop",
                "params": {},
                "caller_app_id": "unknown_network_node",
                "caller_taint": "INTERNAL_AGENT",  # Claiming internal agent
            }
        )

        res_str = ts_transport.handle_inbound_payload(raw_unauth_json, authenticated=False)
        res = json.loads(res_str)

        # Inbound handler clamped caller_taint to UNTRUSTED_EXTERNAL,
        # so TaintLattice blocked the dispatch!
        self.assertFalse(res["success"])
        self.assertIn("Taint violation", res["error"])

        # 2. Authenticated inbound request allows legitimate dispatch
        raw_auth_json = json.dumps(
            {
                "request_id": "req_net_auth",
                "target_capability": "echo",
                "params": {"msg": "trusted tailscale peer"},
                "caller_app_id": "known_tailscale_node",
                "caller_taint": "INTERNAL_AGENT",
            }
        )
        res_auth_str = ts_transport.handle_inbound_payload(raw_auth_json, authenticated=True)
        res_auth = json.loads(res_auth_str)
        self.assertTrue(res_auth["success"])
        self.assertEqual(res_auth["data"]["echo"], "trusted tailscale peer")

        # 3. Inbound request during E-Brake returns structured JSON, not crash
        ts_transport.broadcast_ebrake()
        res_ebrake_str = ts_transport.handle_inbound_payload(raw_auth_json, authenticated=True)
        res_ebrake = json.loads(res_ebrake_str)
        self.assertFalse(res_ebrake["success"])
        self.assertIn("EBrakeTriggeredError", res_ebrake["error"])

        ts_transport.release_ebrake()
        ts_transport.stop()


if __name__ == "__main__":
    unittest.main()

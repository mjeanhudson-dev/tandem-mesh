"""
End-to-end unit tests for the E-Brake lifecycle across Tandem client and transports.
"""

from __future__ import annotations

import unittest

from tandem.client import Tandem
from tandem.core.types import EBrakeTriggeredError
from tandem.transport.pipe import PipeTransport


class TestEBrakeLifecycle(unittest.TestCase):
    def test_memory_ebrake_press_and_release(self) -> None:
        node = Tandem.local(app_id="lifecycle_tester")
        node.register_capability("action", "test action", handler=lambda p: {"status": "done"})

        # Normal call passes
        resp = node.call("action")
        self.assertTrue(resp.success)

        # Press E-Brake
        node.press_ebrake()
        with self.assertRaises(EBrakeTriggeredError):
            node.call("action")

        # Release E-Brake resumes normal operation!
        node.release_ebrake()
        resp_after = node.call("action")
        self.assertTrue(resp_after.success)
        self.assertEqual(resp_after.data["status"], "done")

        node.close()

    def test_pipe_ebrake_press_and_release(self) -> None:
        pipe = PipeTransport(timeout_sec=2.0)
        node = Tandem(transport=pipe, app_id="pipe_lifecycle_tester")
        node.register_capability("pipe_action", "pipe action", handler=lambda p: {"pipe": "ok"})

        resp = node.call("pipe_action")
        self.assertTrue(resp.success)

        # Press E-Brake
        node.press_ebrake()
        with self.assertRaises(EBrakeTriggeredError):
            node.call("pipe_action")

        # Release E-Brake
        node.release_ebrake()
        resp_resumed = node.call("pipe_action")
        self.assertTrue(resp_resumed.success)
        self.assertEqual(resp_resumed.data["pipe"], "ok")

        node.close()


if __name__ == "__main__":
    unittest.main()

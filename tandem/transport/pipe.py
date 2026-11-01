"""
Local IPC & Queue-Based Pipe Transport Adapter.

Supports local cross-thread and cross-process intent streaming via thread-safe queues
and stdio/FIFO emulation with per-request demultiplexing to prevent desynchronization
and queue poisoning.
"""

from __future__ import annotations

import queue
import threading
from typing import Callable, Optional

from tandem.core.types import EBrakeTriggeredError, IntentRequest, IntentResponse
from tandem.transport.base import TransportAdapter


class PipeTransport(TransportAdapter):
    """
    Queue-backed bidirectional pipe transport for asynchronous process isolation.
    Uses request-id keyed dispatch to eliminate race conditions and queue poisoning.
    """

    def __init__(self, timeout_sec: float = 5.0) -> None:
        self.timeout_sec = timeout_sec
        self._inbound_queue: queue.Queue[IntentRequest] = queue.Queue()
        self._pending_responses: dict[str, queue.Queue[IntentResponse]] = {}
        self._lock = threading.Lock()
        self._handler: Optional[Callable[[IntentRequest], IntentResponse]] = None
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._ebrake_active = False

    def start(self) -> None:
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        with self._lock:
            for q in self._pending_responses.values():
                q.put(
                    IntentResponse(
                        request_id="aborted",
                        success=False,
                        error="TransportStoppedError: Pipe transport was stopped.",
                    )
                )
            self._pending_responses.clear()

    def set_handler(self, handler: Callable[[IntentRequest], IntentResponse]) -> None:
        self._handler = handler

    def _process_loop(self) -> None:
        while self._running:
            try:
                req = self._inbound_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if self._ebrake_active:
                resp = IntentResponse(
                    request_id=req.request_id,
                    success=False,
                    error="EBrakeTriggeredError: Pipe halted by E-Brake.",
                )
            elif self._handler:
                try:
                    resp = self._handler(req)
                except Exception as e:
                    resp = IntentResponse(
                        request_id=req.request_id,
                        success=False,
                        error=f"{type(e).__name__}: {str(e)}",
                    )
            else:
                resp = IntentResponse(
                    request_id=req.request_id,
                    success=False,
                    error="NoHandlerError",
                )

            # Route response to the waiting request queue
            with self._lock:
                waiting_queue = self._pending_responses.get(resp.request_id)
                if waiting_queue is not None:
                    waiting_queue.put(resp)

            self._inbound_queue.task_done()

    def send(self, request: IntentRequest) -> IntentResponse:
        if not self._running:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error="TransportNotStartedError",
            )
        if self._ebrake_active:
            raise EBrakeTriggeredError("E-Brake is engaged on pipe transport.")

        resp_queue: queue.Queue[IntentResponse] = queue.Queue(maxsize=1)
        with self._lock:
            self._pending_responses[request.request_id] = resp_queue

        self._inbound_queue.put(request)
        try:
            return resp_queue.get(timeout=self.timeout_sec)
        except queue.Empty:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error=f"TimeoutError: Pipe transport timed out after {self.timeout_sec}s",
            )
        finally:
            with self._lock:
                self._pending_responses.pop(request.request_id, None)

    def broadcast_ebrake(self) -> None:
        self._ebrake_active = True
        # Immediately abort pending callers
        with self._lock:
            for req_id, q in list(self._pending_responses.items()):
                q.put(
                    IntentResponse(
                        request_id=req_id,
                        success=False,
                        error="EBrakeTriggeredError: Pipe halted by E-Brake.",
                    )
                )
            self._pending_responses.clear()

    def release_ebrake(self) -> None:
        self._ebrake_active = False

"""
In-Memory Transport Adapter.

Zero-latency, in-process transport for unit tests, local multi-agent swarms,
and synchronous harness executions.
"""

from __future__ import annotations

from typing import Callable, Optional

from tandem.core.types import EBrakeTriggeredError, IntentRequest, IntentResponse
from tandem.transport.base import TransportAdapter


class MemoryTransport(TransportAdapter):
    """
    Direct in-memory message bus.
    """

    def __init__(self) -> None:
        self._handler: Optional[Callable[[IntentRequest], IntentResponse]] = None
        self._is_running = False
        self._ebrake_active = False

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

    def set_handler(self, handler: Callable[[IntentRequest], IntentResponse]) -> None:
        self._handler = handler

    def send(self, request: IntentRequest) -> IntentResponse:
        if not self._is_running:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error="TransportNotStartedError: Memory transport is offline.",
            )
        if self._ebrake_active:
            raise EBrakeTriggeredError("E-Brake is engaged on memory transport bus.")

        if self._handler is None:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error="NoHandlerError: No router handler attached to memory transport.",
            )

        return self._handler(request)

    def broadcast_ebrake(self) -> None:
        self._ebrake_active = True

    def release_ebrake(self) -> None:
        self._ebrake_active = False

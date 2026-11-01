"""
Transport Seam: The Abstract Transport Adapter for Tandem Mesh.

Per /codebase-design:
  "A seam is a place where you can alter behaviour without editing in that place...
   One adapter means a hypothetical seam. Two adapters means a real one."
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from tandem.core.types import IntentRequest, IntentResponse


class TransportAdapter(ABC):
    """
    Abstract interface at the transport seam.
    Satisfied by MemoryTransport, PipeTransport, and TailscaleHttpTransport.
    """

    @abstractmethod
    def start(self) -> None:
        """Initialize transport listeners/channels."""

    @abstractmethod
    def stop(self) -> None:
        """Close transport and tear down resources."""

    @abstractmethod
    def send(self, request: IntentRequest) -> IntentResponse:
        """Transmit an intent request and wait synchronously for response."""

    @abstractmethod
    def set_handler(self, handler: Callable[[IntentRequest], IntentResponse]) -> None:
        """Register the inbound intent handler (typically IntentRouter.dispatch)."""

    @abstractmethod
    def broadcast_ebrake(self) -> None:
        """Broadcast emergency stop across the transport fabric."""

    @abstractmethod
    def release_ebrake(self) -> None:
        """Release emergency stop across the transport fabric."""

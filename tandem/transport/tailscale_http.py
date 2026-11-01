"""
Layer 7 App-to-App & App-to-Hand over Tailscale / LAN HTTP Bridge Transport.

Architectural Differentiation:
  - Tailscale (L3/L4): Solves machine-to-machine WireGuard mesh encryption and routing
    (e.g., node 100.64.0.12 reaches node 100.64.0.45). It has ZERO understanding of
    what apps are running, what capabilities they possess, their parameter schemas,
    their blast-radius risks, or where the human's physical hand is.
  - Tandem (L7+ / L-Tactile): Runs OVER Tailscale (or LAN/localhost), providing:
      1. Semantic capability discovery and typed RPC.
      2. Monotonic taint lattice enforcement (quarantining unauthenticated network payloads).
      3. Blast-radius haptic telemetry (generating DualSense/Mobile vibration profiles).
      4. Emergency E-Brake mesh synchronization.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from tandem.core.types import (
    EBrakeTriggeredError,
    HapticProfile,
    IntentRequest,
    IntentResponse,
    TaintLevel,
)
from tandem.transport.base import TransportAdapter


class TailscaleHttpTransport(TransportAdapter):
    """
    HTTP/JSON-RPC transport adapter designed to bridge apps across a Tailscale mesh
    or local private network.
    """

    def __init__(
        self,
        peer_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout_sec: float = 5.0,
        target_host: Optional[str] = None,
        target_port: Optional[int] = None,
    ) -> None:
        """
        peer_url: Target Tailscale MagicDNS or 100.x.y.z node URL (e.g. 'http://100.64.0.15:8855')
        auth_token: Cryptographic bearer token for L7 capability authentication.
        """
        if peer_url is None:
            if target_host and target_port:
                peer_url = f"http://{target_host}:{target_port}"
            else:
                peer_url = "http://127.0.0.1:8855"
        self.peer_url = peer_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout_sec = timeout_sec
        self._handler: Optional[Callable[[IntentRequest], IntentResponse]] = None
        self._is_running = False
        self._ebrake_active = False

    def clamp_inbound_taint(self, claimed_taint_name: str, authenticated: bool = False) -> TaintLevel:
        """
        Clamps an inbound payload's claimed taint level. If unauthenticated, clamps to UNTRUSTED_EXTERNAL.
        """
        if authenticated:
            return TaintLevel[claimed_taint_name]
        return TaintLevel.UNTRUSTED_EXTERNAL

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

    def set_handler(self, handler: Callable[[IntentRequest], IntentResponse]) -> None:
        self._handler = handler

    def handle_inbound_payload(self, raw_json: str, authenticated: bool = False) -> str:
        """
        Processes an inbound HTTP payload from a remote Tailscale peer.
        If authenticated=False, the caller taint is clamped to UNTRUSTED_EXTERNAL.
        """
        if self._ebrake_active:
            return json.dumps({
                "request_id": "ebrake",
                "success": False,
                "error": "EBrakeTriggeredError: E-Brake is active across Tailscale mesh bridge.",
            })

        if self._handler is None:
            return json.dumps({"success": False, "error": "NoHandlerError"})

        try:
            data = json.loads(raw_json)
            caller_taint = (
                TaintLevel[data.get("caller_taint", "INTERNAL_AGENT")]
                if authenticated
                else TaintLevel.UNTRUSTED_EXTERNAL
            )

            req = IntentRequest(
                request_id=data["request_id"],
                target_capability=data["target_capability"],
                params=data.get("params", {}),
                caller_app_id=data.get("caller_app_id", "remote_tailscale_peer"),
                caller_taint=caller_taint,
                ratified_by_hand=data.get("ratified_by_hand", False),
            )
            resp = self._handler(req)
            return json.dumps(
                {
                    "request_id": resp.request_id,
                    "success": resp.success,
                    "data": resp.data,
                    "error": resp.error,
                    "taint_level": resp.taint_level.name,
                    "execution_time_ms": resp.execution_time_ms,
                    "haptic_telemetry": (
                        resp.haptic_telemetry.to_dict()
                        if resp.haptic_telemetry
                        else None
                    ),
                }
            )
        except Exception as e:
            return json.dumps({"success": False, "error": f"{type(e).__name__}: {str(e)}"})

    def send(self, request: IntentRequest) -> IntentResponse:
        """Send intent to remote Tailscale peer over HTTP."""
        if not self._is_running:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error="TransportNotStartedError",
            )
        if self._ebrake_active:
            raise EBrakeTriggeredError("E-Brake is actively engaged.")

        endpoint = f"{self.peer_url}/tandem/intent"
        payload = json.dumps(
            {
                "request_id": request.request_id,
                "target_capability": request.target_capability,
                "params": request.params,
                "caller_app_id": request.caller_app_id,
                "caller_taint": request.caller_taint.name,
                "ratified_by_hand": request.ratified_by_hand,
            }
        ).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        req = Request(endpoint, data=payload, headers=headers, method="POST")

        try:
            with urlopen(req, timeout=self.timeout_sec) as response:
                body = response.read().decode("utf-8")
                res_data = json.loads(body)
                haptic_data = res_data.get("haptic_telemetry")
                haptics = HapticProfile.from_dict(haptic_data) if haptic_data else None
                return IntentResponse(
                    request_id=res_data.get("request_id", request.request_id),
                    success=res_data.get("success", False),
                    data=res_data.get("data"),
                    error=res_data.get("error"),
                    taint_level=TaintLevel[res_data.get("taint_level", "INTERNAL_AGENT")],
                    execution_time_ms=res_data.get("execution_time_ms", 0.0),
                    haptic_telemetry=haptics,
                )
        except URLError as err:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error=f"TailscaleHttpTransportError: Failed to reach {self.peer_url}: {err}",
            )
        except Exception as err:
            return IntentResponse(
                request_id=request.request_id,
                success=False,
                error=f"UnexpectedNetworkError: {str(err)}",
            )

    def broadcast_ebrake(self) -> None:
        self._ebrake_active = True
        # Broadcast e-brake to remote peer if reachable
        try:
            endpoint = f"{self.peer_url}/tandem/ebrake"
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            req = Request(endpoint, data=b"{}", headers=headers, method="POST")
            urlopen(req, timeout=1.0)
        except Exception:
            pass  # Best-effort notification

    def release_ebrake(self) -> None:
        self._ebrake_active = False
        try:
            endpoint = f"{self.peer_url}/tandem/release_ebrake"
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            req = Request(endpoint, data=b"{}", headers=headers, method="POST")
            urlopen(req, timeout=1.0)
        except Exception:
            pass  # Best-effort notification

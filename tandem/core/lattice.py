"""
Monotonic Information-Flow Taint Lattice & Structural Invariant Enforcement.

Encodes security and information-flow rules directly into executable structural
checks rather than relying on LLM prompt instructions:
  - T_out = min(T_in_1, T_in_2, ...)
  - Untrusted data cannot trigger privileged capabilities without promotion.
  - Pinpoint promotion requires cryptographic exit-code-0 receipt.
  - Human verification requires fresh physical hand ratification.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Optional

from tandem.core.types import (
    HandDevice,
    TaintAttenuationError,
    TaintLevel,
)


class StructuralTaintLattice:
    """
    Structural enforcer of monotonic information-flow invariants.
    """

    def __init__(self, secret_key: bytes = b"tandem_mesh_hmac_secret_default"):
        self._secret_key = secret_key

    def verify_dispatch_allowed(
        self,
        caller_taint: TaintLevel,
        min_required_taint: TaintLevel,
        capability_name: str,
    ) -> None:
        """
        Verify that caller possesses sufficient trust to invoke target capability.
        Raises TaintAttenuationError if caller_taint < min_required_taint.
        """
        if caller_taint < min_required_taint:
            raise TaintAttenuationError(
                f"Taint violation on '{capability_name}': caller has {caller_taint.name} ({caller_taint.value}), "
                f"but capability requires {min_required_taint.name} ({min_required_taint.value}). "
                f"Untrusted or quarantined data cannot cross into elevated execution boundaries."
            )

    def compute_composed_taint(self, taint_levels: list[TaintLevel]) -> TaintLevel:
        """
        Monotonic taint attenuation: composed data inherits the minimum trust of its inputs.
        T_out = min(T_1, ..., T_n).
        """
        if not taint_levels:
            return TaintLevel.INTERNAL_AGENT
        return min(taint_levels)

    def sign_pinpoint_receipt(
        self,
        artifact_sha256: str,
        test_suite: str,
        passed_checks: int,
        total_checks: int,
    ) -> str:
        """Create an HMAC signature verifying deterministic test execution."""
        payload = f"{artifact_sha256}:{test_suite}:{passed_checks}:{total_checks}"
        return hmac.new(self._secret_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def promote_with_pinpoint(
        self,
        artifact_sha256: str,
        test_suite: str,
        passed_checks: int,
        total_checks: int,
        signature: str,
    ) -> TaintLevel:
        """
        Promotes an INTERNAL_AGENT artifact to PINPOINT_VERIFIED if and only if
        all checks passed (100%) and HMAC signature matches.
        """
        expected_sig = self.sign_pinpoint_receipt(
            artifact_sha256, test_suite, passed_checks, total_checks
        )
        if not hmac.compare_digest(expected_sig, signature):
            raise TaintAttenuationError("Invalid PINPOINT receipt signature: verification rejected.")

        if passed_checks < total_checks or total_checks <= 0:
            raise TaintAttenuationError(
                f"PINPOINT verification incomplete: {passed_checks}/{total_checks} passed."
            )

        return TaintLevel.PINPOINT_VERIFIED

    def promote_with_hand(self, hand: Optional[HandDevice]) -> TaintLevel:
        """
        Promotes an artifact to HUMAN_VERIFIED if the physical hand device
        ratified within the active TTL window.
        """
        if hand is not None and hand.is_ratification_fresh():
            return TaintLevel.HUMAN_VERIFIED
        raise TaintAttenuationError("Human physical ratification missing or expired.")

"""
Unit and structural tests for Tandem type system and monotonic taint lattice.
"""

from __future__ import annotations

import unittest
import time

from tandem.core.types import (
    CapabilityParameter,
    HandDevice,
    SchemaValidationError,
    TaintAttenuationError,
    TaintLevel,
)
from tandem.core.lattice import StructuralTaintLattice


class TestTypesAndLattice(unittest.TestCase):
    def setUp(self) -> None:
        self.lattice = StructuralTaintLattice(secret_key=b"test_secret_key_123")

    def test_parameter_type_validation_success(self) -> None:
        p_str = CapabilityParameter(name="title", type_name="string", description="Title")
        self.assertEqual(p_str.validate("Hello Mesh"), "Hello Mesh")

        p_int = CapabilityParameter(name="count", type_name="int", description="Count")
        self.assertEqual(p_int.validate(42), 42)

        p_float = CapabilityParameter(name="thrust", type_name="float", description="Thrust")
        self.assertEqual(p_float.validate(3.14), 3.14)
        self.assertEqual(p_float.validate(5), 5)  # Int acceptable as float

        p_bool = CapabilityParameter(name="active", type_name="bool", description="Active flag")
        self.assertEqual(p_bool.validate(True), True)

        p_dict = CapabilityParameter(name="meta", type_name="dict", description="Metadata")
        self.assertEqual(p_dict.validate({"k": "v"}), {"k": "v"})

        p_list = CapabilityParameter(name="tags", type_name="list", description="Tags")
        self.assertEqual(p_list.validate(["a", "b"]), ["a", "b"])

    def test_parameter_type_validation_failure(self) -> None:
        p_str = CapabilityParameter(name="title", type_name="string", description="Title")
        with self.assertRaises(SchemaValidationError):
            p_str.validate(12345)

        p_int = CapabilityParameter(name="count", type_name="int", description="Count")
        with self.assertRaises(SchemaValidationError):
            p_int.validate("not an int")
        with self.assertRaises(SchemaValidationError):
            # Guard against bool counting as int
            p_int.validate(True)

        p_required = CapabilityParameter(name="req", type_name="string", description="Required", required=True)
        with self.assertRaises(SchemaValidationError):
            p_required.validate(None)

    def test_parameter_default_value(self) -> None:
        p_opt = CapabilityParameter(
            name="opt", type_name="string", description="Optional", required=False, default="default_val"
        )
        self.assertEqual(p_opt.validate(None), "default_val")

    def test_monotonic_taint_propagation(self) -> None:
        inputs = [TaintLevel.INTERNAL_AGENT, TaintLevel.PINPOINT_VERIFIED, TaintLevel.QUARANTINED_DATA]
        composed = self.lattice.compute_composed_taint(inputs)
        # Minimum of (2, 3, 1) is 1 (QUARANTINED_DATA)
        self.assertEqual(composed, TaintLevel.QUARANTINED_DATA)

        untrusted_mix = [TaintLevel.HUMAN_VERIFIED, TaintLevel.UNTRUSTED_EXTERNAL]
        self.assertEqual(self.lattice.compute_composed_taint(untrusted_mix), TaintLevel.UNTRUSTED_EXTERNAL)

    def test_taint_dispatch_permission_check(self) -> None:
        # Caller with UNTRUSTED_EXTERNAL attempting to invoke INTERNAL_AGENT capability
        with self.assertRaises(TaintAttenuationError):
            self.lattice.verify_dispatch_allowed(
                caller_taint=TaintLevel.UNTRUSTED_EXTERNAL,
                min_required_taint=TaintLevel.INTERNAL_AGENT,
                capability_name="secure_code_executor",
            )

        # Sufficient trust passes without exception
        self.lattice.verify_dispatch_allowed(
            caller_taint=TaintLevel.PINPOINT_VERIFIED,
            min_required_taint=TaintLevel.INTERNAL_AGENT,
            capability_name="secure_code_executor",
        )

    def test_pinpoint_promotion_with_signature(self) -> None:
        artifact_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        suite = "test_cad_engine"

        valid_sig = self.lattice.sign_pinpoint_receipt(
            artifact_sha256=artifact_hash,
            test_suite=suite,
            passed_checks=10,
            total_checks=10,
        )

        promoted = self.lattice.promote_with_pinpoint(
            artifact_sha256=artifact_hash,
            test_suite=suite,
            passed_checks=10,
            total_checks=10,
            signature=valid_sig,
        )
        self.assertEqual(promoted, TaintLevel.PINPOINT_VERIFIED)

        # Fails if checks failed
        with self.assertRaises(TaintAttenuationError):
            self.lattice.promote_with_pinpoint(
                artifact_sha256=artifact_hash,
                test_suite=suite,
                passed_checks=9,
                total_checks=10,
                signature=valid_sig,
            )

        # Fails if forged signature
        with self.assertRaises(TaintAttenuationError):
            self.lattice.promote_with_pinpoint(
                artifact_sha256=artifact_hash,
                test_suite=suite,
                passed_checks=10,
                total_checks=10,
                signature="forged_signature_hex",
            )

    def test_hand_ratification_promotion(self) -> None:
        hand = HandDevice(device_id="dualsense_01", device_type="dualsense")

        # Not yet ratified
        with self.assertRaises(TaintAttenuationError):
            self.lattice.promote_with_hand(hand)

        # Squeeze detent / ratify
        hand.ratify()
        self.assertTrue(hand.is_ratification_fresh(ttl_seconds=5.0))
        promoted = self.lattice.promote_with_hand(hand)
        self.assertEqual(promoted, TaintLevel.HUMAN_VERIFIED)

        # Expired TTL
        hand.last_ratification_timestamp = time.time() - 10.0
        self.assertFalse(hand.is_ratification_fresh(ttl_seconds=5.0))
        with self.assertRaises(TaintAttenuationError):
            self.lattice.promote_with_hand(hand)


if __name__ == "__main__":
    unittest.main()

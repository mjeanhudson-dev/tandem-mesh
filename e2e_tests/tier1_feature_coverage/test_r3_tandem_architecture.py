"""
Tier 1 Feature Coverage: Requirement R3 (Tandem Interoperability Architecture).
Verifies:
- TANDEM_ARCHITECTURE_SPEC.md defines 3-layer stack and contracts
- Tailscale comparative differentiator matrix is formally specified
- OpenAPI 3.1 specification defines endpoints and schemas
- JSON Schema definitions exist for manifests, parameters, requests, and responses
- DualSense Kinematics rules 1-4 are mathematically specified
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add e2e_tests root to sys.path
E2E_ROOT = Path(__file__).resolve().parent.parent
if str(E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(E2E_ROOT))

from common_helpers import TANDEM_ROOT, TANDEM_SPEC_PATH, TANDEM_SCHEMAS_DIR


class TestR3TandemArchitectureFeatures(unittest.TestCase):

    def test_r3_f1_spec_document_defines_3_layer_stack(self):
        """Feature 1: Verify TANDEM_ARCHITECTURE_SPEC.md exists and defines 3-layer stack."""
        self.assertTrue(TANDEM_SPEC_PATH.exists(), f"Spec document not found at {TANDEM_SPEC_PATH}")

        with open(TANDEM_SPEC_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("3-Layer Stack Architecture", content)
        self.assertIn("LAYER 7+", content)
        self.assertIn("TRANSPORT SEAM", content)
        self.assertIn("NETWORK OVERLAY LAYER", content)

    def test_r3_f2_tailscale_comparative_differentiator_matrix(self):
        """Feature 2: Verify specification defines explicit differentiator matrix from Tailscale."""
        with open(TANDEM_SPEC_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Tailscale", content)
        self.assertIn("WireGuard", content)
        # Check comparative dimensions
        self.assertIn("Layer", content)
        self.assertIn("Haptics", content)
        self.assertIn("Taint", content)
        self.assertIn("Blast Radius", content)
        self.assertIn("E-Brake", content)

    def test_r3_f3_openapi_specification_endpoints(self):
        """Feature 3: Verify openapi.yaml exists, is valid YAML/text, and defines core operations."""
        openapi_path = TANDEM_SCHEMAS_DIR / "openapi.yaml"
        self.assertTrue(openapi_path.exists(), f"openapi.yaml not found at {openapi_path}")

        with open(openapi_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("openapi: 3.1", content)
        self.assertIn("/tandem/capabilities", content)
        self.assertIn("/tandem/intent", content)
        self.assertIn("/tandem/hand/bind", content)
        self.assertIn("/tandem/ebrake", content)

    def test_r3_f4_json_schemas_exist_and_are_valid(self):
        """Feature 4: Verify AppManifest, CapabilityParameter, IntentRequest, IntentResponse schemas."""
        required_schemas = [
            "AppManifest.json",
            "CapabilityParameter.json",
            "IntentRequest.json",
            "IntentResponse.json"
        ]
        for schema_name in required_schemas:
            schema_file = TANDEM_SCHEMAS_DIR / schema_name
            self.assertTrue(schema_file.exists(), f"Schema {schema_name} not found")
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            self.assertIn("$schema", schema_data)
            self.assertIn("type", schema_data)

    def test_r3_f5_dualsense_kinematics_rules_specified(self):
        """Feature 5: Verify mathematical formulation of Rules 1-4 in architecture spec."""
        with open(TANDEM_SPEC_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Rule 1: Inverse precompensation
        self.assertIn("Rule 1", content)
        self.assertIn("sqrt", content.lower())
        # Rule 2: C^2 Smootherstep
        self.assertIn("Rule 2", content)
        self.assertIn("6t^5", content)
        # Rule 3: Menu deadzone (15 counts)
        self.assertIn("Rule 3", content)
        self.assertIn("15", content)
        # Rule 4: Sagittal recline projection
        self.assertIn("Rule 4", content)
        self.assertIn("sagittal", content.lower())


if __name__ == "__main__":
    unittest.main()

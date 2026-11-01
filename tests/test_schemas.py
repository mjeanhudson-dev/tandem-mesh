"""
Tests verifying formal API schema definitions and their correspondence with Tandem core types.
"""

import dataclasses
import json
import os
import unittest

from tandem.core.types import (
    AppManifest,
    CapabilityParameter,
    IntentRequest,
    IntentResponse,
)


class TestSchemas(unittest.TestCase):
    """Verifies that all JSON Schema and OpenAPI specifications are valid and match core types."""

    def setUp(self) -> None:
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.schemas_dir = os.path.join(self.base_dir, "schemas")

    def test_json_schemas_exist_and_parse(self) -> None:
        """Verify that all required JSON Schema files exist and parse as valid JSON."""
        expected_schemas = [
            "AppManifest.json",
            "CapabilityParameter.json",
            "IntentRequest.json",
            "IntentResponse.json",
        ]
        for schema_file in expected_schemas:
            path = os.path.join(self.schemas_dir, schema_file)
            self.assertTrue(os.path.exists(path), f"Schema file missing: {schema_file}")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("properties", data)
            self.assertIn("required", data)

    def test_dataclass_fields_covered_by_schemas(self) -> None:
        """Verify 100% field coverage between core dataclasses and exported JSON schemas."""
        mappings = [
            (CapabilityParameter, "CapabilityParameter.json"),
            (AppManifest, "AppManifest.json"),
            (IntentRequest, "IntentRequest.json"),
            (IntentResponse, "IntentResponse.json"),
        ]
        for dc, schema_file in mappings:
            path = os.path.join(self.schemas_dir, schema_file)
            with open(path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            properties = schema["properties"]
            for field in dataclasses.fields(dc):
                self.assertIn(
                    field.name,
                    properties,
                    f"Field '{field.name}' from {dc.__name__} missing in {schema_file}",
                )

    def test_openapi_specification_exists_and_covers_endpoints(self) -> None:
        """Verify that openapi.yaml exists, is non-empty, and contains all required mesh endpoints."""
        openapi_path = os.path.join(self.schemas_dir, "openapi.yaml")
        self.assertTrue(os.path.exists(openapi_path), "openapi.yaml is missing")
        with open(openapi_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 500)
        expected_endpoints = [
            "/tandem/capabilities",
            "/tandem/register",
            "/tandem/intent",
            "/tandem/hand/bind",
            "/tandem/hand/ratify",
            "/tandem/ebrake",
            "/tandem/release_ebrake",
            "/tandem/events",
        ]
        for ep in expected_endpoints:
            self.assertIn(ep, content, f"OpenAPI specification missing endpoint: {ep}")

    def test_architecture_spec_document_exists(self) -> None:
        """Verify that TANDEM_ARCHITECTURE_SPEC.md exists and covers all core architectural sections."""
        spec_path = os.path.join(self.base_dir, "TANDEM_ARCHITECTURE_SPEC.md")
        self.assertTrue(os.path.exists(spec_path), "TANDEM_ARCHITECTURE_SPEC.md is missing")
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = f.read()
        required_topics = [
            "3-Layer Stack Architecture",
            "App-to-App (A2A) Semantic Federation",
            "App-to-Hand (A2H) Tactile Physical Integration",
            "Monotonic Information-Flow Taint Lattice",
            "DualSense Kinematics Engine (Rules 1",
            "Comparative Differentiators: Tailscale vs. Tandem",
            "Sony DualSense USB HID Output Report 0x02 Wire Protocol",
            "5-Speed Autonomy Gearbox",
        ]
        for topic in required_topics:
            self.assertIn(topic, spec, f"Architecture spec missing topic: {topic}")


if __name__ == "__main__":
    unittest.main()

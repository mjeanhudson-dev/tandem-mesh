"""
Tier 2 Boundary & Corner Cases: Requirement R1 (Command Catalog Boundaries).
Tests boundary conditions, missing fields, malformed schemas, and extreme inputs.
"""

import sys
import unittest
from pathlib import Path

# Add e2e_tests root to sys.path
E2E_ROOT = Path(__file__).resolve().parent.parent
if str(E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(E2E_ROOT))

from common_helpers import (
    parse_frontmatter,
    validate_note_frontmatter,
    scrub_credentials,
)

FIXTURES_DIR = E2E_ROOT / "fixtures"


class TestR1CatalogBoundaries(unittest.TestCase):

    def setUp(self):
        # Base valid dictionary for boundary mutation
        self.base_valid = {
            "id": "cmd-powershell-test-cmd",
            "title": "Test-Cmd",
            "description": "Valid function description with sufficient length",
            "use_cases": ["Valid operational use case"],
            "syntax": "Test-Cmd -Flag",
            "execution_environment": "powershell",
            "tags": ["commands/powershell"],
            "timestamps": {"created": "2026-11-01T06:00:00Z", "updated": "2026-11-01T06:00:00Z"},
            "catalog": "aether",
            "type": "command-catalog"
        }

    def test_r1_b1_empty_description_rejected(self):
        """Boundary 1: Empty string description must be rejected."""
        mutated = dict(self.base_valid)
        mutated["description"] = ""
        errors = validate_note_frontmatter(mutated)
        self.assertTrue(any("description" in err.lower() for err in errors), f"Expected description error, got: {errors}")

    def test_r1_b2_short_description_rejected(self):
        """Boundary 2: Description shorter than 5 chars must be rejected."""
        mutated = dict(self.base_valid)
        mutated["description"] = "abc"
        errors = validate_note_frontmatter(mutated)
        self.assertTrue(any("description" in err.lower() for err in errors), f"Expected description error, got: {errors}")

    def test_r1_b3_empty_use_cases_array_rejected(self):
        """Boundary 3: Empty use_cases array [] must be rejected."""
        mutated = dict(self.base_valid)
        mutated["use_cases"] = []
        errors = validate_note_frontmatter(mutated)
        self.assertTrue(any("use_cases" in err.lower() for err in errors), f"Expected use_cases error, got: {errors}")

    def test_r1_b4_short_use_case_item_rejected(self):
        """Boundary 4: Use case item with length < 3 chars must be rejected."""
        mutated = dict(self.base_valid)
        mutated["use_cases"] = ["ab"]
        errors = validate_note_frontmatter(mutated)
        self.assertTrue(any("use case" in err.lower() for err in errors), f"Expected use case length error, got: {errors}")

    def test_r1_b5_invalid_execution_environment_rejected(self):
        """Boundary 5: Unsupported shells (e.g. zsh, fish, cmd.exe) must be rejected."""
        mutated = dict(self.base_valid)
        mutated["execution_environment"] = "zsh"
        errors = validate_note_frontmatter(mutated)
        self.assertTrue(any("execution environment" in err.lower() for err in errors), f"Expected env error, got: {errors}")

    def test_r1_b6_missing_frontmatter_delimiters_returns_none(self):
        """Boundary 6: Markdown file missing --- delimiters fails extraction cleanly."""
        missing_fm_path = FIXTURES_DIR / "sample_harnesses" / "missing_protocol_harness.md"
        with open(missing_fm_path, "r", encoding="utf-8") as f:
            content = f.read()
        fm, body = parse_frontmatter(content)
        self.assertIsNone(fm)
        self.assertEqual(body, content)

    def test_r1_b7_complex_credential_scrubbing_boundary(self):
        """Boundary 7: Scrubber handles multiple tokens, trailing quotes, and multi-line assignments."""
        raw = (
            'export OPENAI_API_KEY="sk-proj-123456789012345678901234567890"\n'
            '$dbPassword = "P@ssw0rd999!Secret"\n'
            'curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTIzfQ"\n'
            'git clone https://ghp_abcdefghijklmnopqrstuvwxyz0123456789@github.com/repo.git\n'
        )
        scrubbed = scrub_credentials(raw)
        self.assertNotIn("sk-proj-1234567890", scrubbed)
        self.assertNotIn("P@ssw0rd999!", scrubbed)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", scrubbed)
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz0123456789", scrubbed)
        self.assertIn("[REDACTED_API_KEY]", scrubbed)
        self.assertIn("[REDACTED_SECRET]", scrubbed)
        self.assertIn("[REDACTED_TOKEN]", scrubbed)
        self.assertIn("[REDACTED_GH_TOKEN]", scrubbed)


if __name__ == "__main__":
    unittest.main()

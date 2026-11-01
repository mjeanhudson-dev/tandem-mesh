"""
Tier 2 Boundary & Corner Cases: Requirement R2 (Agent Harness Boundaries).
Tests missing tokens, empty configs, incomplete directives, and malformed files.
"""

import sys
import json
import unittest
from pathlib import Path

# Add e2e_tests root to sys.path
E2E_ROOT = Path(__file__).resolve().parent.parent
if str(E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(E2E_ROOT))

from common_helpers import validate_agent_harness_directive

FIXTURES_DIR = E2E_ROOT / "fixtures"


class TestR2HarnessBoundaries(unittest.TestCase):

    def test_r2_b1_empty_content_flags_missing_protocol(self):
        """Boundary 1: Completely empty file content must fail validation."""
        errors = validate_agent_harness_directive("")
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("token" in err.lower() for err in errors))

    def test_r2_b2_missing_protocol_token_flagged(self):
        """Boundary 2: Harness without Aether protocol token is flagged."""
        fixture_path = FIXTURES_DIR / "sample_harnesses" / "missing_protocol_harness.md"
        with open(fixture_path, "r", encoding="utf-8") as f:
            content = f.read()

        errors = validate_agent_harness_directive(content)
        self.assertTrue(any("token" in err.lower() for err in errors))

    def test_r2_b3_directive_missing_function_requirement_flagged(self):
        """Boundary 3: Directive missing Function labeling requirement is flagged."""
        content = (
            "<!-- AETHER_COMMAND_PROTOCOL_START -->\n"
            "## Command Protocol\n"
            "- Use Cases: describe use cases\n"
            "- Syntax: invocation\n"
            "- Execution Environment: pwsh\n"
            "Check Obsidian Aether Catalog before writing scripts.\n"
        )
        errors = validate_agent_harness_directive(content)
        self.assertTrue(any("function" in err.lower() for err in errors))

    def test_r2_b4_directive_missing_use_cases_requirement_flagged(self):
        """Boundary 4: Directive missing Use Cases requirement is flagged."""
        content = (
            "<!-- AETHER_COMMAND_PROTOCOL_START -->\n"
            "## Command Protocol\n"
            "- Function: describe what it does\n"
            "- Syntax: invocation\n"
            "- Execution Environment: pwsh\n"
            "Check Obsidian Aether Catalog before writing scripts.\n"
        )
        errors = validate_agent_harness_directive(content)
        self.assertTrue(any("use case" in err.lower() for err in errors))

    def test_r2_b5_directive_missing_obsidian_lookup_flagged(self):
        """Boundary 5: Directive missing Obsidian catalog check is flagged."""
        content = (
            "<!-- AETHER_COMMAND_PROTOCOL_START -->\n"
            "## Command Protocol\n"
            "- Function: describe what it does\n"
            "- Use Cases: describe operational trigger\n"
            "- Syntax: invocation\n"
            "- Execution Environment: pwsh\n"
            "No mention of central vault.\n"
        )
        errors = validate_agent_harness_directive(content)
        self.assertTrue(any("obsidian" in err.lower() or "catalog" in err.lower() for err in errors))

    def test_r2_b6_corrupted_toml_detected(self):
        """Boundary 6: Corrupted TOML syntax in config fixture is detected."""
        toml_path = FIXTURES_DIR / "sample_harnesses" / "corrupted_config.toml"
        self.assertTrue(toml_path.exists())
        with open(toml_path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Check for unclosed quote boundary
        quote_count = raw.count('"')
        self.assertNotEqual(quote_count % 2, 0, "Corrupted TOML fixture must have unbalanced quotes")

    def test_r2_b7_corrupted_json_detected(self):
        """Boundary 7: Corrupted JSON syntax in settings fixture is detected."""
        json_path = FIXTURES_DIR / "sample_harnesses" / "corrupted_settings.json"
        self.assertTrue(json_path.exists())
        with open(json_path, "r", encoding="utf-8") as f:
            with self.assertRaises(json.JSONDecodeError):
                json.load(f)


if __name__ == "__main__":
    unittest.main()

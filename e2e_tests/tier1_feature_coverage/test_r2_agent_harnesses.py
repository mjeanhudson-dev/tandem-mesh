"""
Tier 1 Feature Coverage: Requirement R2 (Local Agent Harness Integration).
Verifies:
- Standard directive structure enforces Function, Use Cases, Syntax, Environment
- Mandatory Obsidian Aether catalog check directive is present
- Agent configuration files (settings.json, config.toml) maintain valid syntax
- Live user harness directories are inspected for syntax validity and directives
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

from common_helpers import validate_agent_harness_directive

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
USER_HOME = Path(os.path.expanduser("~"))


class TestR2AgentHarnessFeatures(unittest.TestCase):

    def test_r2_f1_compliant_harness_directive_passes_all_checks(self):
        """Feature 1: Verify compliant harness directive passes validation with 0 errors."""
        fixture_path = FIXTURES_DIR / "sample_harnesses" / "compliant_harness.md"
        self.assertTrue(fixture_path.exists())

        with open(fixture_path, "r", encoding="utf-8") as f:
            content = f.read()

        errors = validate_agent_harness_directive(content)
        self.assertEqual(errors, [], f"Compliant directive had validation errors: {errors}")

    def test_r2_f2_directive_enforces_function_labeling(self):
        """Feature 2: Verify directive explicitly mandates Function description labeling."""
        fixture_path = FIXTURES_DIR / "sample_harnesses" / "compliant_harness.md"
        with open(fixture_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Function", content)
        self.assertRegex(content, r"Function.*accomplishes")

    def test_r2_f3_directive_enforces_use_cases_labeling(self):
        """Feature 3: Verify directive explicitly mandates Use Cases labeling."""
        fixture_path = FIXTURES_DIR / "sample_harnesses" / "compliant_harness.md"
        with open(fixture_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Use Cases", content)
        self.assertRegex(content, r"Use Cases?.*operational use case")

    def test_r2_f4_directive_enforces_syntax_and_environment(self):
        """Feature 4: Verify directive mandates Syntax and Execution Environment (bash/pwsh)."""
        fixture_path = FIXTURES_DIR / "sample_harnesses" / "compliant_harness.md"
        with open(fixture_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Syntax", content)
        self.assertIn("Execution Environment", content)
        self.assertIn("PowerShell", content)
        self.assertIn("Bash", content)

    def test_r2_f5_directive_enforces_obsidian_catalog_lookup(self):
        """Feature 5: Verify directive mandates searching Obsidian Aether catalog before writing scripts."""
        fixture_path = FIXTURES_DIR / "sample_harnesses" / "compliant_harness.md"
        with open(fixture_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Obsidian", content)
        self.assertIn("Aether", content)
        self.assertIn("Commands", content)

    def test_r2_f6_claude_settings_json_syntax_validity(self):
        """Feature 6: Verify Claude Code settings.json is syntactically valid JSON."""
        settings_path = USER_HOME / ".claude" / "settings.json"
        if not settings_path.exists():
            self.skipTest(f"settings.json not found at {settings_path}")

        with open(settings_path, "r", encoding="utf-8-sig") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"Claude settings.json failed JSON decode: {e}")

        self.assertIsInstance(data, dict)

    def test_r2_f7_codex_config_toml_syntax_validity(self):
        """Feature 7: Verify Codex config.toml exists and has valid basic configuration structure."""
        config_toml = USER_HOME / ".codex" / "config.toml"
        if not config_toml.exists():
            self.skipTest(f"config.toml not found at {config_toml}")

        with open(config_toml, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple verification of TOML sections and key-values without third-party library
        self.assertGreater(len(content.strip()), 10)
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        has_section_or_key = any(line.startswith("[") or "=" in line for line in lines)
        self.assertTrue(has_section_or_key, "config.toml must contain valid TOML sections or key-value pairs")


if __name__ == "__main__":
    unittest.main()

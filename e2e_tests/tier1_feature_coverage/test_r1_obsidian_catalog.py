"""
Tier 1 Feature Coverage: Requirement R1 (Command Labeling Rules & Obsidian Cataloging).
Verifies:
- AetherCommandSchema.json conforms to Draft 2020-12
- Frontmatter schema validation requires non-empty description and use_cases
- Export-AetherCommand.ps1 structure and parameters
- aether_export.sh structure and CLI wrappers
- Retroactive scanner AST capabilities
- Credential scrubber masks secrets
- Valid note fixtures pass 100% of schema checks
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

from common_helpers import (
    AETHER_SCHEMA_PATH,
    OBSIDIAN_VAULT_COMMANDS,
    parse_frontmatter,
    validate_note_frontmatter,
    scrub_credentials,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class TestR1ObsidianCatalogFeatures(unittest.TestCase):

    def test_r1_f1_schema_exists_and_is_draft_2020_12(self):
        """Feature 1: Verify AetherCommandSchema.json exists and conforms to Draft 2020-12."""
        self.assertTrue(AETHER_SCHEMA_PATH.exists(), f"Schema not found at {AETHER_SCHEMA_PATH}")
        with open(AETHER_SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

        self.assertIn("$schema", schema)
        self.assertIn("2020-12", schema["$schema"])
        self.assertEqual(schema.get("type"), "object")

        required = schema.get("required", [])
        expected_required = [
            "id", "title", "description", "use_cases", "syntax",
            "execution_environment", "tags", "timestamps", "catalog", "type"
        ]
        for field in expected_required:
            self.assertIn(field, required, f"Field '{field}' must be in schema required list")

        # Verify minItems and minLength constraints
        properties = schema.get("properties", {})
        self.assertGreaterEqual(properties["description"].get("minLength", 0), 5)
        self.assertGreaterEqual(properties["use_cases"].get("minItems", 0), 1)

    def test_r1_f2_valid_note_frontmatter_passes_100_percent(self):
        """Feature 2: Verify compliant note frontmatter passes validation with 0 errors."""
        valid_note_path = FIXTURES_DIR / "sample_notes" / "valid_note.md"
        self.assertTrue(valid_note_path.exists())

        with open(valid_note_path, "r", encoding="utf-8") as f:
            content = f.read()

        fm, body = parse_frontmatter(content)
        self.assertIsNotNone(fm, "Failed to parse YAML frontmatter")

        errors = validate_note_frontmatter(fm)
        self.assertEqual(errors, [], f"Valid note had validation errors: {errors}")
        self.assertGreaterEqual(len(fm["description"]), 5)
        self.assertGreaterEqual(len(fm["use_cases"]), 1)

    def test_r1_f3_powershell_export_cmdlet_specification(self):
        """Feature 3: Verify Export-AetherCommand.ps1 exists and defines required parameters."""
        export_ps1 = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\aether_tools\Export-AetherCommand.ps1")
        self.assertTrue(export_ps1.exists(), f"Cmdlet not found at {export_ps1}")

        with open(export_ps1, "r", encoding="utf-8") as f:
            content = f.read()

        # Check required cmdlet elements
        self.assertIn("Export-AetherCommand", content)
        self.assertIn("[CmdletBinding()]", content)
        self.assertIn("Description", content)
        self.assertIn("UseCases", content)
        self.assertIn("Syntax", content)
        self.assertIn("VaultPath", content)

    def test_r1_f4_bash_export_hook_specification(self):
        """Feature 4: Verify aether_export.sh exists and defines on-the-fly export functions."""
        export_sh = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\aether_tools\aether_export.sh")
        self.assertTrue(export_sh.exists(), f"Bash hook not found at {export_sh}")

        with open(export_sh, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("aether_export_command", content)
        self.assertIn("aether-cmd", content)
        self.assertIn("AETHER_VAULT_PATH", content)

    def test_r1_f5_retroactive_ast_scanner_specification(self):
        """Feature 5: Verify Invoke-AetherRetroactiveCatalog.ps1 specifies AST parsing."""
        scanner_ps1 = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\aether_tools\Invoke-AetherRetroactiveCatalog.ps1")
        self.assertTrue(scanner_ps1.exists(), f"Scanner not found at {scanner_ps1}")

        with open(scanner_ps1, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("AETHER RETROACTIVE SCRIPT CATALOGER", content)
        # Check AST parser usage
        self.assertIn("System.Management.Automation.Language.Parser", content)
        self.assertIn("ParseFile", content)

    def test_r1_f6_credential_sanitizer_scrubs_secrets(self):
        """Feature 6: Verify credential scrubber removes API keys, tokens, and passwords."""
        leak_fixture = FIXTURES_DIR / "sample_commands" / "credential_leak_script.ps1"
        self.assertTrue(leak_fixture.exists())

        with open(leak_fixture, "r", encoding="utf-8") as f:
            raw_script = f.read()

        scrubbed = scrub_credentials(raw_script)

        # Assert no sensitive patterns remain
        self.assertNotIn("sk-ant-api03", scrubbed)
        self.assertNotIn("ghp_1234567890", scrubbed)
        self.assertNotIn("P@ssw0rd1234!", scrubbed)
        self.assertIn("[REDACTED_API_KEY]", scrubbed)
        self.assertIn("[REDACTED_GH_TOKEN]", scrubbed)
        self.assertIn("[REDACTED_SECRET]", scrubbed)

    def test_r1_f7_vault_commands_validation(self):
        """Feature 7: If catalog notes exist in Obsidian vault, 100% must have non-empty fn and use cases."""
        if not OBSIDIAN_VAULT_COMMANDS.exists():
            self.skipTest(f"Obsidian catalog directory {OBSIDIAN_VAULT_COMMANDS} not yet created.")

        notes = list(OBSIDIAN_VAULT_COMMANDS.rglob("*.md"))
        if not notes:
            self.skipTest("No notes in vault yet (scanner may be actively running).")

        passed = 0
        failures = []
        for note in notes:
            with open(note, "r", encoding="utf-8") as f:
                content = f.read()
            fm, _ = parse_frontmatter(content)
            if not fm:
                failures.append(f"{note.name}: Missing frontmatter")
                continue
            errs = validate_note_frontmatter(fm)
            if errs:
                failures.append(f"{note.name}: {errs}")
            else:
                passed += 1

        self.assertEqual(len(failures), 0, f"Vault notes failed validation: {failures}")
        self.assertGreater(passed, 0)


if __name__ == "__main__":
    unittest.main()

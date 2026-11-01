"""
Tier 3 Cross-Feature Interaction: Command Export + Obsidian Cataloging + Harness Discovery.
Verifies pairwise interaction between:
- Shell command export generation
- Obsidian markdown note schema validation
- Agent harness discovery and retrieval of cataloged commands
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add e2e_tests root to sys.path
E2E_ROOT = Path(__file__).resolve().parent.parent
if str(E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(E2E_ROOT))

from common_helpers import parse_frontmatter, validate_note_frontmatter


class TestExportAndHarnessLookup(unittest.TestCase):

    def setUp(self):
        self.temp_vault = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_vault.name)
        self.cmd_dir = self.vault_path / "Aether" / "Commands" / "PowerShell"
        self.cmd_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_vault.cleanup()

    def test_i1_exported_note_is_valid_and_discoverable_by_agent_harness(self):
        """Interaction: Command exported to vault validates against schema and is queried by simulated agent."""
        # 1. Simulate on-the-fly command export
        note_content = (
            "---\n"
            'id: "cmd-powershell-restart-pool"\n'
            'title: "Restart-AppPool"\n'
            'description: "Recycles specified IIS Application Pool to clear degraded worker state"\n'
            "use_cases:\n"
            '  - "Recovering from memory exhaustion in worker process"\n'
            '  - "Deploying hotfixed DLL assemblies without full server reboot"\n'
            'syntax: "Restart-WebAppPool -Name <PoolName>"\n'
            'execution_environment: "powershell"\n'
            "tags:\n"
            '  - "commands/powershell"\n'
            '  - "type/system"\n'
            "timestamps:\n"
            '  created: "2026-11-01T06:30:00Z"\n'
            '  updated: "2026-11-01T06:30:00Z"\n'
            "parameters:\n"
            '  - name: "-Name"\n'
            '    type: "string"\n'
            "    required: true\n"
            '    description: "Application pool name"\n'
            'catalog: "aether"\n'
            'type: "command-catalog"\n'
            'version: "1.0.0"\n'
            "---\n\n"
            "# Restart-AppPool\n\n"
            "## Description\n"
            "Recycles specified IIS Application Pool to clear degraded worker state.\n"
        )
        note_file = self.cmd_dir / "restart-pool.md"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write(note_content)

        # 2. Schema Validation Gate
        fm, _ = parse_frontmatter(note_content)
        self.assertIsNotNone(fm)
        errors = validate_note_frontmatter(fm)
        self.assertEqual(errors, [], f"Exported note failed validation: {errors}")

        # 3. Simulated Agent Harness Catalog Discovery Query
        # Agent queries the vault catalog for commands matching keyword 'IIS' or 'AppPool'
        discovered = []
        for file in self.cmd_dir.glob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                c = f.read()
            parsed_fm, _ = parse_frontmatter(c)
            if parsed_fm:
                # Search keyword in description, title, or use_cases
                text_to_search = (
                    parsed_fm.get("title", "") + " " +
                    parsed_fm.get("description", "") + " " +
                    " ".join(parsed_fm.get("use_cases", []))
                ).lower()
                if "apppool" in text_to_search or "iis" in text_to_search:
                    discovered.append(parsed_fm)

        self.assertEqual(len(discovered), 1)
        match = discovered[0]
        self.assertEqual(match["id"], "cmd-powershell-restart-pool")
        self.assertEqual(match["syntax"], "Restart-WebAppPool -Name <PoolName>")
        self.assertEqual(len(match["use_cases"]), 2)


if __name__ == "__main__":
    unittest.main()

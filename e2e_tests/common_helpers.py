"""
Common Test Helpers and Utilities for Aether & Tandem E2E Test Suite.
Zero external third-party dependencies required.
"""

import os
import re
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Authoritative Paths
AETHER_SCHEMA_PATH = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\aether_tools\AetherCommandSchema.json")
TANDEM_ROOT = Path(r"C:\Users\Zachariah\.gemini\antigravity\scratch\tandem")
TANDEM_SPEC_PATH = TANDEM_ROOT / "TANDEM_ARCHITECTURE_SPEC.md"
TANDEM_SCHEMAS_DIR = TANDEM_ROOT / "schemas"
OBSIDIAN_VAULT_COMMANDS = Path(r"C:\Users\Zachariah\Documents\obsidian memory complex\Aether\Commands")


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Parses YAML frontmatter between leading --- delimiters.
    Uses lightweight stdlib regex parser supporting string, int, bool, list, and nested maps.
    Handles UTF-8 BOM if present.
    Returns (frontmatter_dict, body_markdown).
    """
    content = content.lstrip('\ufeff \t\r\n')
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", content, re.DOTALL)
    if not match:
        return None, content

    yaml_block = match.group(1)
    body = match.group(2)
    fm = {}

    # Basic YAML parser for Obsidian notes
    current_key = None
    in_list = False
    in_submap = False
    submap_key = None

    for line in yaml_block.splitlines():
        line_clean = line.rstrip()
        if not line_clean or line_clean.strip().startswith("#"):
            continue

        # Check for top-level key: value
        top_key_match = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", line_clean)
        if top_key_match:
            k = top_key_match.group(1)
            v = top_key_match.group(2).strip()
            current_key = k
            in_list = False
            in_submap = False

            if v == "":
                # Could be start of list or submap
                fm[k] = []
                continue
            elif v.startswith("[") and v.endswith("]"):
                # Inline JSON-style array: ["a", "b"]
                try:
                    fm[k] = json.loads(v)
                except Exception:
                    # Strip brackets and quotes
                    raw_items = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    fm[k] = raw_items
            elif (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                fm[k] = v[1:-1]
            elif v.lower() == "true":
                fm[k] = True
            elif v.lower() == "false":
                fm[k] = False
            elif re.match(r"^-?\d+$", v):
                fm[k] = int(v)
            else:
                fm[k] = v
            continue

        # Check for list item: "  - value"
        list_match = re.match(r"^\s+-\s*(.*)$", line_clean)
        if list_match and current_key:
            item_val = list_match.group(1).strip()
            if (item_val.startswith('"') and item_val.endswith('"')) or (item_val.startswith("'") and item_val.endswith("'")):
                item_val = item_val[1:-1]
            if not isinstance(fm.get(current_key), list):
                fm[current_key] = []
            fm[current_key].append(item_val)
            continue

        # Check for sub-map item: "  key: value"
        submap_match = re.match(r"^\s+([a-zA-Z0-9_-]+):\s*(.*)$", line_clean)
        if submap_match and current_key:
            sub_k = submap_match.group(1)
            sub_v = submap_match.group(2).strip()
            if (sub_v.startswith('"') and sub_v.endswith('"')) or (sub_v.startswith("'") and sub_v.endswith("'")):
                sub_v = sub_v[1:-1]
            if not isinstance(fm.get(current_key), dict):
                fm[current_key] = {}
            fm[current_key][sub_k] = sub_v
            continue

    return fm, body


def validate_note_frontmatter(fm: Dict[str, Any]) -> List[str]:
    """
    Validates a parsed frontmatter dictionary against AetherCommandSchema requirements.
    Returns list of violation strings (empty if valid).
    """
    errors = []
    if not isinstance(fm, dict):
        return ["Frontmatter is not a dictionary"]

    # 1. Required fields
    required = ["id", "title", "description", "use_cases", "syntax", "execution_environment", "tags", "timestamps"]
    for field in required:
        if field not in fm:
            errors.append(f"Missing required field: {field}")

    # 2. Description (Function) non-empty and min length
    desc = fm.get("description", "")
    if not isinstance(desc, str) or len(desc.strip()) < 5:
        errors.append("Field 'description' must be a non-empty string with min length 5")

    # 3. Use cases non-empty array with length >= 1
    use_cases = fm.get("use_cases")
    if not isinstance(use_cases, list) or len(use_cases) < 1:
        errors.append("Field 'use_cases' must be an array with at least 1 item")
    else:
        for idx, uc in enumerate(use_cases):
            if not isinstance(uc, str) or len(uc.strip()) < 3:
                errors.append(f"Use case at index {idx} must be a string with min length 3")

    # 4. Syntax non-empty
    syntax = fm.get("syntax", "")
    if not isinstance(syntax, str) or len(syntax.strip()) < 1:
        errors.append("Field 'syntax' must be a non-empty string")

    # 5. Execution environment enum
    env = fm.get("execution_environment", "")
    valid_envs = ["powershell", "pwsh", "bash", "sh", "cmd"]
    if env not in valid_envs:
        errors.append(f"Execution environment '{env}' not in {valid_envs}")

    # 6. ID format
    note_id = fm.get("id", "")
    if not isinstance(note_id, str) or not re.match(r"^cmd-(bash|powershell|pwsh|sh|cmd)-[a-z0-9_.-]+$", note_id):
        errors.append(f"Invalid id pattern: '{note_id}'")

    # 7. Timestamps
    ts = fm.get("timestamps")
    if not isinstance(ts, dict) or "created" not in ts or "updated" not in ts:
        errors.append("Field 'timestamps' must contain 'created' and 'updated'")

    return errors


def validate_agent_harness_directive(content: str) -> List[str]:
    """
    Validates whether an agent harness configuration contains the required
    Aether Command Protocol directives and tokens.
    """
    errors = []
    has_token = "AETHER_COMMAND_PROTOCOL_START" in content or "Command Labeling & Obsidian Aether Catalog Protocol" in content
    if not has_token:
        errors.append("Missing Aether command protocol token")

    # Check for mandatory labeling fields mentioned
    if not re.search(r"Function", content, re.IGNORECASE):
        errors.append("Directive missing 'Function' labeling requirement")
    if not re.search(r"Use Cases?", content, re.IGNORECASE):
        errors.append("Directive missing 'Use Cases' labeling requirement")
    if not re.search(r"Syntax", content, re.IGNORECASE):
        errors.append("Directive missing 'Syntax' labeling requirement")
    if not re.search(r"Execution Environment", content, re.IGNORECASE):
        errors.append("Directive missing 'Execution Environment' labeling requirement")

    # Check for Obsidian catalog query requirement
    if not re.search(r"Obsidian.*Aether.*Catalog|Aether.*Commands", content, re.IGNORECASE):
        errors.append("Directive missing Obsidian Aether catalog lookup mandate")

    return errors


def scrub_credentials(text: str) -> str:
    """
    Reference Python credential scrubbing implementation matching scanner specifications.
    """
    # Scrub OpenAI / Anthropic / Generic API keys
    text = re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]", text)
    # Scrub GitHub tokens
    text = re.sub(r"gh[pousr]_[a-zA-Z0-9]{36,}", "[REDACTED_GH_TOKEN]", text)
    # Scrub Bearer tokens
    text = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer [REDACTED_TOKEN]", text)
    # Scrub Password variables
    text = re.sub(r'(\$(?:password|dbPassword|secret|token)\s*=\s*)"[^"]+"', r'\1"[REDACTED_SECRET]"', text, flags=re.IGNORECASE)
    return text

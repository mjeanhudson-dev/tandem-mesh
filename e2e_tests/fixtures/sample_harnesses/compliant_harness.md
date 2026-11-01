# Master Developer Directives

<!-- AETHER_COMMAND_PROTOCOL_START -->
## Command Labeling & Obsidian Aether Catalog Protocol

All bash and PowerShell commands formulated, executed, or recommended in this environment MUST adhere to the **Aether Command Catalog Standards**:

1. **Mandatory Command Labeling Invariant**:
   Whenever emitting, running, or presenting shell commands or reusable scripts, you MUST provide explicit metadata:
   - **`Function`**: Exactly one clear sentence defining what the command accomplishes.
   - **`Use Cases`**: At least one concrete operational use case, failure mode recovery, or workflow trigger.
   - **`Syntax`**: Exact command invocation signature with named parameters and placeholders.
   - **`Execution Environment`**: Explicitly identify whether execution target is `PowerShell` or `Bash`.

2. **Obsidian Aether Catalog Query & Reuse**:
   - The central command knowledge catalog resides in the Obsidian Vault at:
     `C:\Users\Zachariah\Documents\obsidian memory complex\Aether\Commands\`
   - Before writing ad-hoc multi-line shell scripts, search the catalog (`find_by_name` or `grep_search` in the vault) to reuse tested commands.

3. **On-the-Fly Cataloging**:
   - When introducing a novel, reusable, or complex command, export it to the Aether catalog or include the `# @fn: <description>; @use: <use_case>` header decorator so that the shell hook automatically registers it into Obsidian.
<!-- AETHER_COMMAND_PROTOCOL_END -->

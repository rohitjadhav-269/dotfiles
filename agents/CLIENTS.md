# Agent client projections

`AGENTS.md` and the top-level `rules/*.md` files are the canonical rulebook. Client projections are delivery mechanisms only; they do not own membership or applicability.

| Client | Ownership | Bootstrap / refresh | Verification |
|---|---|---|---|
| Generic `~/.agents` consumers | Manifest-managed | `make link` installs the whole `agents/` directory at `~/.agents` | `bash scripts/link.sh --check` |
| Claude Code | Manifest-managed compatibility links | `make link` installs `~/.claude/CLAUDE.md`, `skills`, `agents`, and `commands` from the canonical tree | `bash scripts/link.sh --check` |
| Codex | Manifest-managed bootstrap bridge | `make link` installs `config/codex/AGENTS.md` at `~/.codex/AGENTS.md`; the bridge invokes `init-rulebook` and retains optional local `RTK.md` guidance | `bash scripts/link.sh --check`; confirm a new task loads the canonical rulebook |
| Zed Agent (native) | Manifest-managed bootstrap bridge | `make link` installs `config/zed/AGENTS.md` at `~/.config/zed/AGENTS.md`; the bridge invokes `init-rulebook` at session start and after compaction and applies optional RTK guidance to terminal commands | `bash scripts/link.sh --check`; confirm a new native Zed Agent thread loads the canonical rulebook |
| Zed External Agents (ACP) | Agent-owned native configuration | Zed hosts the thread, but each external agent owns its instruction loader; Codex continues to use the Codex bridge and native config rather than Zed's personal `AGENTS.md` | Confirm the selected external agent loads its own native instructions |
| Cursor skills | Manifest-managed compatibility link | `make link` installs `~/.cursor/skills` from the canonical skills tree | `bash scripts/link.sh --check` |
| Cursor rules | Manifest-managed file plus account startup pointer | `make link` installs `config/cursor/rulebook.mdc` at `~/.cursor/rules/rulebook.mdc`. In Customize → Rules, set the startup User Rule to `config/cursor/user-rule.txt`; account rules are vendor-synced, not restored by the linker. | `make agent-clients-check`; inspect the account pointer and a fresh session outside this repo |
| VS Code Copilot | Manifest-managed user bridge | `make link` installs `config/copilot/copilot-instructions.md` at `~/.copilot/copilot-instructions.md`, the personal always-on entrypoint for the Copilot harness. Other harnesses retain their own instruction discovery. | `make agent-clients-check`; Agent Customizations → Instructions and a fresh Copilot session |
| Antigravity | Manifest-managed user bridge | `make link` installs `config/antigravity/GEMINI.md` at `~/.gemini/GEMINI.md`. Read the loader skill directly if skill invocation is unavailable. | `make agent-clients-check`; fresh session when Antigravity is installed |
| Nimbalyst | Host-managed | No stable repository-owned projection path is declared; the host may consume `~/.agents` | Confirm the active task exposes the current rulebook before relying on Nimbalyst-specific rules |

The macOS manifest owns bridge placement, not runtime acceptance. Cursor's account
User Rule is a separate vendor setting; use the tracked startup text and preserve
unrelated account rules. Do not link the entire canonical rules directory into an
always-on rules folder. Windows consumer paths are unchanged.

`make agent-clients-check` verifies managed symlinks and matching contents for
Codex, Claude Code, Zed, Cursor, Copilot and Antigravity. Claude Code retains the
public canonical-index link. Skills and MCP connectivity do not prove instruction
loading. Antigravity's `~/.gemini/GEMINI.md` can also affect other Gemini clients.

Verify each installed client with a fresh session outside this repository: inspect
the startup source, index and always-on reads, one matching conditional rule,
deferred action gates, and rehydration after compaction. Account settings, remote
profiles, harness differences and fresh-machine behavior require separate checks.
This public projection has fixture coverage, not a live-client acceptance claim.

# 05 - Paseo orchestration

Activate only when the task uses Paseo agents, worktrees, loops, schedules, heartbeats, provider discovery, browser tools, MCP injection, or daemon diagnostics.

## Scope

Paseo owns agent, worktree, loop, schedule, heartbeat, and daemon lifecycle state. Use Paseo tools or the `paseo` CLI for those surfaces instead of editing `~/.paseo` state files directly or substituting ad hoc git worktree management.

Generic host-tooling rules still apply to sandbox false-negatives, browser access, and GitHub auth checks, but they do not override Paseo's orchestration contract.

## Provider selection

- Before a Paseo skill chooses a provider or creates an agent, read `~/.paseo/orchestration-preferences.json` unless the user explicitly named a provider.
- If the preferences file is missing, say so once and use the Paseo skill defaults.
- Provider IDs, modes, thinking options, and feature flags must come from orchestration preferences or provider inspection. Do not hardcode new provider choices into helper skills.
- Only set provider-specific feature IDs returned by provider inspection.

## Worktrees and branches

- Apply `07-worktree-lifecycle.md` to resolve and validate the placement and branch name for every Paseo-created or selected worktree, and `03-worktree-hygiene.md` for checkout safety. Use Paseo `create_worktree` or `create_agent.workspace.source.kind = "worktree"` only when it can honor both, and validate the returned `worktreePath` before use; otherwise report the limitation instead of creating an externally placed worktree or silently working in place.
- Branch names passed to Paseo must follow the repo's branch policy. Prefer workflow namespaces such as `feature/<slug>`, `bugfix/<slug>`, `hotfix/<slug>`, or `release/<version>` when the repo expects git-flow naming.
- Treat agent/operator namespaces such as `codex/*`, `claude/*`, `cursor/*`, `gemini/*`, `ash/*`, or `tash/*` as forbidden fallbacks; use a contributor namespace only when repository policy explicitly requires it.
- Avoid generic `fix/<slug>` unless the repo explicitly uses that namespace.
- Treat the returned Paseo `branchName`, `worktreePath`, and `workspaceId` as authoritative. Do not assume they match the requested slug.
- Do not place an agent in a worktree by using `workspace: { kind: "current", cwd: "<worktreePath>" }`; use a Paseo-created or existing workspace instead.

## Agent lifecycle

- Use `relationship: { kind: "subagent" }` for advisors, committees, planners, implementers, auditors, and loop workers whose lifetime belongs to the current task.
- Use `relationship: { kind: "detached" }` for handoffs and delegations the user may continue after the current agent is archived.
- Leave `notifyOnFinish` omitted or set to `true` unless the work is truly fire-and-forget.
- Prefer asynchronous completion notifications. Do not repeatedly poll running agents just to check whether they are done.
- Archive agents only when the workflow calls for it or the user asks.

## Browser and MCP tooling

- If Paseo browser tools or MCP injection are available for a Paseo-managed agent, prefer that Paseo-provided route for that agent's browser checks before external browser fallbacks.
- If Paseo browser tooling fails because of sandbox, host access, writable state, or MCP routing, treat it as a tooling-context signal first and then use the generic host-tooling fallback rules.

## Host tooling

Apply [Host tooling](04-host-tooling.md) for host-native execution, sandbox recovery, authentication, and browser access. Keep the Paseo browser/MCP preference above when that managed route is available.

## Daemon safety

- Never restart or kill the Paseo daemon without explicit user approval. Restarting the daemon can interrupt every running agent, including the one asking.
- Diagnose daemon issues in this order: daemon log, `paseo daemon status`, then the health endpoint.
- Do not modify `~/.paseo/agents`, `~/.paseo/projects`, schedules, loops, PID files, or key files directly unless the user explicitly asks for low-level repair after diagnostics.

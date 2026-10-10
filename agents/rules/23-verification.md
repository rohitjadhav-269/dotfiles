# 23 — Verification before completion

Activate when code, config, automation, data transforms, or generated artifacts are changed.

- **Verify the behavior you touched.** Run the narrowest meaningful test, build, lint, typecheck, script, preview, or command that proves the requested change works.
- **Wait for observable conditions, not guessed delays.** In tests, scripts, and monitors, synchronize on the event or state that proves readiness, using fresh observations, a bounded timeout, and an actionable timeout error. Use a fixed sleep only when elapsed time is itself the behavior under test or an external contract requires it; first synchronize on the triggering condition and document the known timing basis.
- **Prefer project-defined commands.** Use the repo's documented verification path first. If none exists, choose the smallest local check that exercises the changed surface and say what it covers.
- **Do not claim unrun checks.** Report exactly what passed, failed, or was skipped. If a check could not run because of missing deps, network, credentials, time, or sandbox limits, say so plainly.
- **Investigate failures in scope.** If a verification command fails, determine whether the failure is caused by your change, pre-existing state, environment, or an unrelated area before reporting it.
- **Keep evidence concise.** Summarize the important command names and outcomes; include raw output only when the specific lines explain the result.

## Evidence and test value

- **Reviews follow content.** Record scope and the inspected revision plus staged, unstaged, and relevant untracked changes. Reuse a verdict only while its supporting inputs remain unchanged; the same commit alone is insufficient. After repairs, re-review the affected scope and dependencies. Report incomplete reviews honestly; a saved status or another model's agreement is not proof.
- **Tests protect contracts.** Before adding a test, name the observable behavior or independent contract, the credible regression that makes it fail, and the gap in existing coverage. Prefer extending an existing test; avoid implementation mirrors and production seams used only by tests. Exact-output tests remain valid when those bytes are the contract. Add no tests solely for count or coverage targets.
- **Prove regressions when feasible.** A regression test should fail for the original defect in its own assertion and pass after repair. Collection, fixture, and environment failures are not regression proof. Rerun the original probe and relevant adjacent behavior; report unavailable proof explicitly.
- **Close against acceptance.** Summarize delivered criteria, remaining concerns, and unrun checks. Completion requires evidence; blocked work names the actual blocker, attempted checks, and next action. A full workflow status template is unnecessary for small changes.

## Cross-client continuity

For substantial work crossing phases, clients, or sessions, leave one compact handoff in the project's existing documentation or memory convention: deliverable/mode, scope, owner, decisions and rationale, acceptance criteria, artifact paths, evidence, unresolved work, and next action. Reference artifacts instead of copying them. Include the inspected revision and relevant working-tree changes when Git applies; revalidate changed inputs before continuing. Chat suffices for small work; create no parallel memory store or client-specific rule copies.

Capture verified lessons that prevent repeated friction through existing project memory and client learning policy. No lesson is a valid outcome; learning never authorizes governing-rule edits.

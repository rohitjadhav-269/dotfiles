# 07 — Worktree lifecycle

Action-gated. Load immediately before creating a git worktree, creating a branch for isolation, finishing development work, creating a PR/MR or editing its title, merging a pull request, cleaning up branches/worktrees, or producing a handoff after that work.

## Worktree creation

Apply this section whenever the agent creates a git worktree or selects its placement. A user request for a worktree authorizes creation of the isolated checkout; do not ask for a second confirmation.

- **Reuse existing isolation.** Resolve `git rev-parse --git-dir`, `git rev-parse --git-common-dir`, `git rev-parse --show-superproject-working-tree`, and `git rev-parse --show-toplevel` first. If `GIT_DIR != GIT_COMMON` and the checkout is not a submodule, reuse the current linked worktree instead of nesting another one. Report an unexpected detached HEAD before editing.
- **Always use a project-local parent.** Create manual worktrees inside the same repository/project directory under `<repo-root>/.worktrees/` or `<repo-root>/worktrees/`. For a canonical repository under `~/Projects/`, the required parent is exactly `<repo-root>/.worktrees/`. Elsewhere, selection order is: an explicit user or project convention, then an existing allowed directory, then the `.worktrees/` default. If both allowed directories already exist and no convention selects one, prefer `.worktrees/`. Never choose an adjacent sibling checkout, a global worktree directory, `.worktree/`, `.context/`, or a temporary directory. A host-native worktree tool is acceptable only when it can honor the selected project-local path and branch policy; otherwise use `git worktree` directly. Paseo-managed worktrees also remain subject to the additional lifecycle rules in `05-paseo-orchestration.md`.
- **Require ignore coverage.** Before creation, verify the selected parent with `git check-ignore -q <worktree-parent>/` (or a representative child path). If it is not ignored, add the selected parent (`.worktrees/` or `worktrees/`) to the repo's appropriate ignore file before creating the worktree; do not commit that change unless the user separately authorized a commit.
- **Make the path mirror the full repository-selected branch name.** Classify and name the branch under the Branch creation rules below, then use `<repo-root>/<worktree-parent>/<full-branch-name>` as the worktree path—for example, branch `feature/catalog-search` under `.worktrees/` maps to `.worktrees/feature/catalog-search`. Create any required directory inside the selected parent; do not flatten `/` to `-` or invent an agent/operator prefix.
- **Create branch and worktree atomically when the repository workflow permits it.** After resolving the repository-selected branch name and base ref and confirming that neither the branch nor path conflicts, use `git worktree add -b <full-branch-name> <repo-root>/<worktree-parent>/<full-branch-name> <base-ref>`. If the repository requires another branch-creation tool, use that workflow and then attach the resulting branch with `git worktree add <repo-root>/<worktree-parent>/<full-branch-name> <full-branch-name>`.
- **Do not silently abandon isolation.** If creation is blocked by permissions, sandbox policy, branch ownership, a dirty/conflicted target, or an unsupported host tool, report the exact blocker. Do not continue in the current checkout when the user asked for a worktree.
- **Prepare and verify before implementation.** In the new checkout, follow `22-environment.md` for project-aware dependency/setup commands and `23-verification.md` for the narrowest meaningful clean-baseline check. If the baseline fails, distinguish a pre-existing failure from setup trouble and ask before implementing on a known-bad baseline.

## Branch creation

- **Repository rules select branch creation.** Resolve the workflow, branch type and prefix, base, and naming convention from repository instructions and existing configuration. Do not replace them with an agent or global convention.
- **Do not invent an agent or operator namespace.** Names such as `claude/*`, `cursor/*`, `codex/*`, `gemini/*`, `tash/*`, or `ash/*` are forbidden fallbacks. Use a contributor namespace only when the repository explicitly requires it.
- **Workflow commands do not relax authorization.** Before using Git Flow or another branch-management tool, inspect its effects and obtain any separately required authorization for commits, pushes, tags, merges, or deletions. If the repository-required tool is unavailable, stop rather than substituting another workflow.

## Finishing development work

Apply this section when implementation is complete and integration, publication, or cleanup is being considered.

- **Repository rules select shared-branch synchronization.** Follow the procedure they select; when they explicitly select rebase, use fetch → rebase → resolve → verify → stage → commit. If no procedure is defined and the synchronization choice matters, stop and request direction instead of choosing a history shape. If the selected procedure cannot run safely because the repo is offline, local-only, detached, has no upstream, or contains unrelated user work, follow the repository's documented exception or stop and report the condition. If local `<default>` diverged after a squash PR merge, follow **Default-branch realignment after squash PR merge** below instead of rebasing.
- **Repository rules select integration.** Resolve the target branch, allowed mechanism, merge shape, authoritative verification, and branch/worktree retention or cleanup policy from the repository before acting. The global rulebook supplies worktree, identity, signing, and authorization discipline; it does not replace repository policy with a preferred hosting or terminal workflow. If repository and attribution requirements conflict, use the outcome classification and terminal-handoff rule in `02-attribution.md`.
- **Resolve and serialize the target checkout.** Use `git worktree list --porcelain -z` to determine whether a checkout owns the target branch. If a clean usable checkout owns it, use that checkout. If none owns it, a suitable clean compliant checkout, including the canonical checkout, may switch to it under repository rules; do not create a linked worktree solely to give the target an owner. Do not try to check out the same target in a second worktree. When multiple branches target the same branch, refresh, verify, integrate, and post-verify one branch completely before starting the next. If the owning checkout is dirty or selection of a suitable checkout is unclear, report the state instead of adding another worktree or cleanup automation.
- **Select merge checks from actual CI/CD.** Follow **Merge verification** below before integration and before post-merge cleanup.
- **Integration remains the user's decision.** If the user has not explicitly authorized merge, push/PR creation, or another integration path, preserve the branch and worktree and ask one focused question about how they want the completed work integrated. Do not infer integration authorization from implementation completion.
- **Follow repository PR retention policy.** After pushing and opening a pull/merge request, preserve its branch and worktree for review unless repository policy explicitly permits earlier removal of a clean, fully published, session-owned branch or worktree.
- **Require explicit confirmation before discarding unfinished work.** Before destructive discard, show the exact branch, its commits that would be lost, and the worktree path, then ask for explicit confirmation. Do not treat vague cleanup language as authorization to force-delete commits or a worktree.
- **Prove integration and ownership before normal cleanup.** Do not remove a branch or worktree until the work is proven integrated and session ownership is proven under the rules below, unless repository retention policy explicitly permits earlier removal and the work is clean, fully published, and session-owned. Explicitly confirmed discard is the only other exception to the integration requirement; ownership and destructive-action authorization still must be proven.

## Merge verification

- **Budget the whole merge task.** Default: 10 minutes total active elapsed time per merge task; one full-suite attempt and no automatic full-suite retries. Start accounting before CI/CD discovery; count execution, diagnosis, fixes, waiting on checks, and post-merge verification. Pause only while awaiting user input. Share one remaining time allowance and full-suite count across turns, candidates, and authorized subagents; continuations and delegation do not reset either.
- **Carry one budget record.** Create a shared budget record before the first budgeted action in the task status or handoff; create that record under the project's existing convention if absent. Record task identity (repository, target branch, and request scope), time used and remaining with an observation timestamp, full-suite and focused-rerun counts (used and reserved), approved extensions, and reusable evidence. The coordinator updates the record and reserves attempts before launch or delegation. Include the current record in every continuation, resumption or compaction handoff, and subagent prompt. Delegates inherit only the recorded remaining allowance and reserved attempts, and return usage and results to the coordinator.
- **Recover before continuing.** Before budgeted execution in a continuation, resumed session, compaction recovery, or subagent, restore and validate the record. If it is missing, incomplete, or stale, attempt read-only recovery from task history, time observations, and run logs. If remaining time or attempt counts cannot be recovered, stop and ask before further budgeted work. A missing record never grants a fresh allowance; only a confirmed new merge task receives the default budget.
- **Enforce the remaining allowance.** Bound each local run or provider wait by the remaining time; if expected cost exceeds it or cannot reasonably be bounded, ask before starting. At exhaustion, stop safely, preserve logs and state, and leave integration or cleanup pending. Any second full-suite execution requires explicit approval, including after a passing run, fix, rebase, or merge. Repository-required checks do not expand the allowance. Ask one focused question through the available harness question tool, with a recommendation and expected additional cost; extensions or extra attempts require explicit finite limits.
- **Discover applicable CI/CD first.** Inspect the target repository's pipeline configuration at the target ref and candidate merge result, or verified provider configuration. Resolve event, branch, path, and job conditions for this merge. A standalone script such as `verify:ci`, a documented `verify` alias, or a broad test target does not establish that CI/CD exists. An empty hosted-check list alone does not establish its absence; unavailable configuration means discovery is incomplete.
- **Ask when CI/CD is absent or unknown.** If no applicable pipeline is confirmed, report what was inspected and explicitly ask: "No applicable CI/CD was found for this merge. Which checks should I run?" Propose the smallest relevant checks with their expected cost; wait for the user's answer before running merge-time checks or integrating. A request to merge or silence does not authorize a fallback suite. Honor an explicit check selection already given for this same scope; ask again if that scope changes.
- **Emulate only configured validation.** Local CI/CD emulation is permitted only for an applicable pipeline confirmed above. Map its validation jobs to their actual commands, preserving configured scope and conditions; announce those commands and known or estimated cost before execution. Follow referenced scripts only as part of those jobs, rather than promoting an unrelated verification wrapper into a merge gate. Deployment, publication, and other remote mutations retain their separate authorization requirements. If a required job cannot run locally or through the configured provider, report the gap and ask how to proceed.
- **Require passing evidence before integration.** The selected checks are the applicable configured validation jobs, or the checks explicitly chosen by the user when no applicable CI/CD is confirmed. Every selected check must have valid passing local or hosted evidence before integration. Run selected checks that lack valid reusable evidence under the reuse rules below. Failed, pending, skipped, or unavailable selected checks block integration; report the unresolved gap. Discovery, command mapping, or receiving the user's check selection alone does not satisfy this requirement.
- **Reuse evidence before rerunning.** Record the tested revision/tree, commands, relevant configuration, environment, and outcomes. Reuse passing local or hosted evidence when those inputs still match and repository policy permits. A local merge alone does not require another full run. Recheck the merged result's relevant inputs; rerun only selected checks invalidated by changes or explicitly required by repository policy or the user's agreed check selection. Apply the same CI/CD discovery and explicit-ask boundary after merge.
- **Bound failure recovery.** On failure, stop integration or cleanup, preserve the branch/worktree and logs, and report the failing stage and a scoped next step. Retry a failed stage only after an identified in-scope fix or verified transient cause. Allow at most one focused rerun per merge task, within the remaining budget. After a failed full-suite run, ask before another full-suite attempt, broadening validation, or starting an autonomous retry loop. An unchanged failure is a stop condition, not a reason to repeat the suite.

## Creating PRs/MRs or editing their titles

Apply to CLI, API/connector, browser, and app UI operations, including drafts and PR-only work.

1. Load `02-attribution.md` and its message/emoji contract before preparing the title.
2. Validate the exact outgoing title against that contract before every creation or title edit. Supply the validated title explicitly; review generated or prefilled titles before submitting.
3. After each write, read the saved title from the provider and compare it exactly with the validated title, then recheck the contract. On GitHub, use `gh pr view <PR> --json title --jq .title` or an equivalent provider read. A successful write response alone is insufficient.
4. Correct any mismatch and repeat verification within the authorized operation. Report unresolved mismatches, failed corrections, or unavailable readback as incomplete title verification.

## Merging pull requests

Apply when preparing a PR/MR merge or verifying a completed one, including merges performed by the provider or user. Execution requires the user's explicit merge authorization under `01-authorization`.

- **Use the repository-selected mechanism.** A request to merge a PR authorizes its repository-selected merge mechanism, subject to the attribution, authorization, and safety rules above; it does not make `gh`, the web UI, automatic merge, merge queues, strategy flags, or branch deletion authoritative over repository rules. Use the repository's documented path and only its permitted merge shape and cleanup behavior.
- **Prepare the integration subject.** Load `02-attribution.md` and its message/emoji contract. For merge and squash commits, require exactly one trailing ` (#NNN)` with the original PR/MR numeric ID, including for MRs. Count the suffix within the existing subject-length limit. Supply the validated subject explicitly wherever the selected mechanism permits, including manual terminal handoffs. Preserve the repository-approved merge shape and scoped commits. Example:

  ```text
  chore(main): 🔀 merge homepage optimizations and hero refinements (#207)
  ```

- When the repository-selected mechanism is hosted and completes asynchronously, poll the provider for its merged state rather than inferring success from the immediate return. Do not poll until green and then run a second manual merge unless the user explicitly asked to watch first.
- For GitHub CLI, `<PR>` is the PR number, URL, or branch name. Omit it when checked out on the PR head branch only when `gh pr merge …` can resolve the PR from context.
- If the repository-selected hosted merge fails, report the error and stop. Do not improvise another mechanism, bypass checks, or use an administrative override unless the user explicitly asks and repository policy permits it.
- After merge, confirm the provider's PR state with the repository-selected tooling. On GitHub, use `gh pr view <PR> --json state,mergedAt,mergeCommit,headRefName` when helpful (`MERGED` is a GitHub PR state, not a git merge result). If local `<default>` looks diverged after a squash merge, follow **Default-branch realignment after squash PR merge** below before treating it as a failed merge. Other local post-merge cleanup still follows **Post-merge cleanup** below (`git branch -d`, worktree removal, etc.).
- **Verify the actual integration subject.** Resolve the completed request's merge/squash commit SHA from the provider and read its actual subject from that commit in the target repository or provider commit API. Recheck the message/emoji contract and original request ID suffix; compare the complete subject exactly with the validated subject when one was prepared. A saved PR/MR title alone is insufficient. For fast-forward/rebase merges without a dedicated integration commit, report the suffix check as not applicable and preserve the original commits. On a mismatch or unavailable readback, report incomplete merge-subject verification and stop before cleanup. Fixing published history requires separate authorization; never silently amend or force-push it.
- **Apply attribution before choosing hosting.** If the repository-selected hosted merge would violate `02-attribution.md`, do not invoke it. Apply the outcome classification there: provide its terminal handoff when manual terminal merge is required, otherwise report the actual blocker. Do not perform or automate the local integration.

GitHub's non-interactive evidence and explicitly authorized `gh pr merge` commands live in `rules/03-worktree-hygiene/github-preflight.md`. Terminal integration strategies live in `rules/03-worktree-hygiene/terminal-integration.md`. Those references supply commands, not policy.

## Post-merge cleanup

When the user asks for post-merge cleanup, branch/worktree hygiene, stale branch cleanup, or whether anything remains after merge:

- Inspect current status, local branches, remote-tracking branches, worktrees, and stashes before deleting anything. Report the full picture before any deletion.
- Fetch before judging stale state: `git fetch origin --prune` when network/auth is available. If fetch is unavailable, say the cleanup is based on local remote-tracking refs.
- Resolve the integration branch from the repo, don't assume `main` — check `git symbolic-ref refs/remotes/origin/HEAD` or the repo's configured default (`master`, `develop`, etc.). `<default>` below means that resolved local integration branch; `origin/<default>` is its remote-tracking ref.

### Determining session ownership

A branch or worktree "belongs to the current agent session" only if you can attribute it to work done in *this* conversation — e.g. you created it, you committed to it, or it matches a session worktree path/naming convention used here. If you cannot positively attribute it, treat it as **not session-owned** and apply the more conservative rule. When ownership is genuinely ambiguous, list it for follow-up rather than guessing.

### Verifying code is on `<default>`

Confirm reachability with `git`; when integration used a pull or merge request, confirm its state with the repository-selected provider tooling. Do not treat provider metadata field names as git ref paths.

`git branch --merged <default>` only detects fast-forward/merge-commit integration. PR merges are frequently **squash or rebase merges**, where the original branch tips will never show as merged. Before concluding a branch is *not* merged, cross-check with `git cherry -v <default> <branch>` or PR metadata such as `gh pr view <PR> --json state,mergedAt,headRefName` when `gh` is available. For `git cherry -v`: empty output means the branch has no commits not reachable from `<default>`; lines prefixed with `-` mean patch-equivalent commits are already upstream, which is common after squash/rebase merges; lines prefixed with `+` are not upstream. Prefer `git cherry -v` or PR metadata for squash/rebase merges. Treat raw diff checks as supporting evidence only, and state the exact diff form used. State which method confirmed the merge.

### Default-branch realignment after squash PR merge

Provider-created squash merges (including `gh pr merge --auto --squash --delete-branch` on GitHub) land on `origin/<default>` as a new commit. Local `<default>` may still point at the pre-squash tip and appear diverged — that is usually realignment, not a failed merge.

Confirm pull- or merge-request state with the repository-selected provider tooling first, then confirm git refs and local branch state. On GitHub, use `gh`; do not treat provider metadata field names as git ref paths.

Before any destructive ref move, confirm:

- Repository-selected provider tooling confirms integration; on GitHub, `gh pr view <PR> --json state,mergedAt,mergeCommit,headRefName` reports `MERGED`
- `git fetch origin --prune`
- If not on `<default>`, switch only when the worktree is clean; otherwise stop and report
- On `<default>` (re-check after any switch): `git status --short --branch` shows no staged or unstaged tracked changes
- On `<default>`: `git cherry -v origin/<default> <default>` is empty or shows only `-` lines (patch-equivalent commits already upstream)

If all pass: report that the changes are already on `origin/<default>` and **ask before** `git reset --hard origin/<default>`. Do not run it silently — it rewrites the local branch ref and discards uncommitted state.

If any `git cherry -v` line is prefixed with `+`, or the worktree/index is dirty, stop and list the local commits or files that need a human decision.

### Decision matrix

- Session-owned, code is on `<default>`, and repository policy permits cleanup → delete the branch/worktree.
- Repository policy requires retaining the branch or worktree → leave it in place.
- Not session-owned but code is already on `<default>` → delete only when the user explicitly asked for cleanup.
- Not session-owned and code is **not** on `<default>` → leave alone and list for follow-up.
- Local commits, uncommitted files, staged files, conflicts, or stashes found → leave alone and list for follow-up. Do not analyze, drop, restore, or delete them unless asked. Dirty state blocks cleanup only for the branch/worktree that contains it. Stashes are never dropped during cleanup; list them separately. Unrelated stashes or dirty files do not by themselves block deletion of a verified merged clean branch. A session-owned branch with extra unmerged local commits or a dirty worktree is **not** safe to delete — list it instead.

### Safe deletion mechanics

- Prefer safe deletion: use `git branch -d`, not `git branch -D`, unless the user explicitly confirms force deletion. A `-d` failure ("not fully merged") is a signal to stop and re-check the merged state, not to escalate to `-D`.
- You cannot delete the branch that is currently checked out. If cleanup targets the current branch, switch to `<default>` first; if that would disturb uncommitted user work, stop and report instead.
- Remove worktrees before deleting the branch they reference. Use `git worktree remove <path>` (no `--force`) — a removal that fails on a dirty/locked worktree means it has uncommitted state: leave it and list it. Run `git worktree prune` after worktree cleanup.
- Local-only by default. Do not delete remote branches or push deletions (`git push origin --delete`, `git push origin :branch`) unless the user explicitly asks or the repository-selected integration or cleanup contract includes topic-branch deletion. Do not duplicate a deletion already performed by that mechanism.
- After local cleanup, run `git remote prune origin --dry-run` (or `git fetch --prune --dry-run`) to surface remote-tracking refs that are already gone upstream, and list remote branches whose code is on `<default>` but still exist on the remote. Report these as a separate "remote, needs your call" list and ask before acting — never fold remote deletion into the local pass.

## Handoff state

Before handing work back after branch, worktree, integration, PR, merge, or cleanup work:

- Confirm the current branch and upstream.
- Confirm whether the worktree is clean or list remaining uncommitted/staged files.
- Confirm whether the branch is aligned with upstream, ahead, behind, or diverged. If local `<default>` diverged after a squash PR merge, follow **Default-branch realignment after squash PR merge** before treating divergence as unresolved work.
- Mention remaining stashes, stale branches, or worktrees without deleting them unless the cleanup rules above apply.

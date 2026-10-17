"""Public-owned isolated fixtures for merge rule contracts."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def run(*args, **kwargs):
    kwargs.setdefault("stdin", subprocess.DEVNULL)
    return subprocess.run(args, text=True, capture_output=True, **kwargs)

class MergeRuleContracts(unittest.TestCase):
    @staticmethod
    def _copy_rulebook_contract_fixture(checkout: Path) -> Path:
        script = checkout / "scripts/audit-rules.sh"
        script.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/audit-rules.sh", script)
        shutil.copy2(
            ROOT / "scripts/test-agent-terminal-integration.sh",
            script.parent / "test-agent-terminal-integration.sh",
        )
        agents = checkout / "agents"
        agents.mkdir()
        shutil.copy2(ROOT / "agents/AGENTS.md", agents / "AGENTS.md")
        shutil.copytree(ROOT / "agents/rules", agents / "rules")
        skills = agents / "skills"
        skills.mkdir()
        for source in (ROOT / "agents/skills").iterdir():
            if not (source / "SKILL.md").is_file():
                continue
            target = skills / source.name
            target.mkdir()
            (target / "SKILL.md").write_text("")
        init_skill = agents / "skills/init-rulebook/SKILL.md"
        shutil.copy2(ROOT / "agents/skills/init-rulebook/SKILL.md", init_skill)
        return script


    def test_rule_audit_rejects_missing_pr_title_contracts(self) -> None:
        cases = (
            ("agents/AGENTS.md", "creating a PR/MR or editing its title", "both action gates"),
            (
                "agents/rules/02-attribution.md",
                "commit message or PR/MR title",
                "dispatcher must route PR/MR titles",
            ),
            (
                "agents/rules/attribution/message.md",
                "commit subjects and pull/merge request (PR/MR) titles",
                "must share the emoji contract",
            ),
            (
                "agents/rules/attribution/message.md",
                "Before committing or creating/editing a PR/MR title",
                "validated before creation or edits",
            ),
            (
                "agents/rules/attribution/message.md",
                "including the custom mappings above",
                "must apply the custom emoji mappings",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "compare it exactly with the validated title",
                "compare the saved provider title",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "Correct any mismatch and repeat verification",
                "mismatches must be corrected and reverified",
            ),
            (
                "agents/rules/02-attribution.md",
                "PR/MR merge work loads message/emoji and identity/signing",
                "merges must load message and identity contracts",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "exactly one trailing ` (#NNN)` with the original PR/MR numeric ID",
                "integration subjects must end with the original request ID",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "read its actual subject",
                "must read the actual integration commit subject",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "compare the complete subject exactly with the validated subject",
                "must compare the complete integration subject",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "report the suffix check as not applicable",
                "must report suffix verification as not applicable",
            ),
            (
                "agents/rules/07-worktree-lifecycle.md",
                "report incomplete merge-subject verification and stop before cleanup",
                "verification failures must block cleanup",
            ),
        )
        with tempfile.TemporaryDirectory() as td:
            checkout = Path(td) / "checkout"
            script = self._copy_rulebook_contract_fixture(checkout)
            env = {**os.environ, "DOTFILES": str(checkout)}
            baseline = run("bash", str(script), env=env)
            self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
            for relative, clause, diagnostic in cases:
                with self.subTest(path=relative, clause=clause):
                    path = checkout / relative
                    original = path.read_text()
                    self.assertIn(clause, original)
                    path.write_text(original.replace(clause, "", 1))
                    result = run("bash", str(script), env=env)
                    path.write_text(original)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(diagnostic, result.stderr)


    def test_rule_audit_requires_pipeline_discovery_and_bounded_merge_checks(self) -> None:
        # The operator contract is the regression: no inferred suite or retry
        # loop may replace the required decision when applicable CI is absent.
        lifecycle = "agents/rules/07-worktree-lifecycle.md"
        cases = (
            (
                lifecycle,
                "10 minutes total active elapsed time per merge task",
                "ten-minute cumulative time budget",
            ),
            (
                lifecycle,
                "one full-suite attempt and no automatic full-suite retries",
                "limit full-suite attempts and automatic retries",
            ),
            (
                lifecycle,
                "Share one remaining time allowance and full-suite count across turns, candidates, and authorized subagents",
                "shared rather than reset by continuation or delegation",
            ),
            (
                lifecycle,
                "Create a shared budget record before the first budgeted action",
                "create its budget record before spending",
            ),
            (
                lifecycle,
                "task identity (repository, target branch, and request scope), time used and remaining with an observation timestamp, full-suite and focused-rerun counts (used and reserved), approved extensions, and reusable evidence",
                "carry task identity, time and attempt accounting",
            ),
            (
                lifecycle,
                "The coordinator updates the record and reserves attempts before launch or delegation",
                "reserved before execution or delegation",
            ),
            (
                lifecycle,
                "Include the current record in every continuation, resumption or compaction handoff, and subagent prompt",
                "continuations and subagents must receive the current budget record",
            ),
            (
                lifecycle,
                "If remaining time or attempt counts cannot be recovered, stop and ask before further budgeted work",
                "missing merge accounting must require recovery or an explicit ask",
            ),
            (
                lifecycle,
                "A missing record never grants a fresh allowance",
                "missing merge budget records must not reset allowances",
            ),
            (
                lifecycle,
                "Bound each local run or provider wait by the remaining time",
                "enforce the remaining time allowance",
            ),
            (
                lifecycle,
                "if expected cost exceeds it or cannot reasonably be bounded, ask before starting",
                "unbounded or over-budget merge work must require an explicit ask",
            ),
            (
                lifecycle,
                "Any second full-suite execution requires explicit approval",
                "require approval even after a passing run",
            ),
            (
                lifecycle,
                "At exhaustion, stop safely, preserve logs and state, and leave integration or cleanup pending",
                "stop work without bypassing merge requirements",
            ),
            (
                lifecycle,
                "Allow at most one focused rerun per merge task, within the remaining budget",
                "focused merge-check recovery must remain bounded",
            ),
            (
                lifecycle,
                "Inspect the target repository's pipeline configuration at the target ref and candidate merge result",
                "discover CI/CD for the actual target and merge result",
            ),
            (
                lifecycle,
                "Resolve event, branch, path, and job conditions for this merge",
                "resolve pipeline applicability",
            ),
            (
                lifecycle,
                "A standalone script such as `verify:ci`, a documented `verify` alias, or a broad test target does not establish that CI/CD exists",
                "must not infer CI/CD from a verification script",
            ),
            (
                lifecycle,
                "If no applicable pipeline is confirmed, report what was inspected and explicitly ask:",
                "require an explicit ask and answer",
            ),
            (
                lifecycle,
                "wait for the user's answer before running merge-time checks or integrating",
                "require an explicit ask and answer",
            ),
            (
                lifecycle,
                "Local CI/CD emulation is permitted only for an applicable pipeline confirmed above",
                "require a confirmed applicable pipeline",
            ),
            (
                lifecycle,
                "Every selected check must have valid passing local or hosted evidence before integration",
                "configured and user-selected checks must pass before integration",
            ),
            (
                lifecycle,
                "the applicable configured validation jobs, or the checks explicitly chosen by the user when no applicable CI/CD is confirmed",
                "configured and user-selected checks must pass before integration",
            ),
            (
                lifecycle,
                "Run selected checks that lack valid reusable evidence",
                "without reusable evidence must execute before integration",
            ),
            (
                lifecycle,
                "Failed, pending, skipped, or unavailable selected checks block integration",
                "unresolved selected checks must block integration",
            ),
            (
                lifecycle,
                "A local merge alone does not require another full run",
                "reuse valid evidence instead of unconditional reruns",
            ),
            (
                lifecycle,
                "After a failed full-suite run, ask before another full-suite attempt",
                "require an ask before another full attempt",
            ),
            (
                "agents/rules/23-verification.md",
                "Ordinary change verification does not authorize a full integration suite",
                "defer merge check selection to lifecycle policy",
            ),
        )
        with tempfile.TemporaryDirectory() as td:
            checkout = Path(td) / "checkout"
            script = self._copy_rulebook_contract_fixture(checkout)
            env = {**os.environ, "DOTFILES": str(checkout)}
            baseline = run("bash", str(script), env=env)
            self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
            for relative, clause, diagnostic in cases:
                with self.subTest(path=relative, clause=clause):
                    path = checkout / relative
                    original = path.read_text()
                    self.assertIn(clause, original)
                    path.write_text(original.replace(clause, "", 1))
                    result = run("bash", str(script), env=env)
                    path.write_text(original)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(diagnostic, result.stderr)

            # Reject reinstating either old mandate even alongside the new rules.
            path = checkout / lifecycle
            original = path.read_text()
            for legacy in (
                "Before integrating, run the repository-defined integration or CI-equivalent gate.",
                "After any local merge, rerun the same integration/CI-equivalent gate.",
            ):
                with self.subTest(legacy=legacy):
                    path.write_text(original + "\n" + legacy + "\n")
                    result = run("bash", str(script), env=env)
                    path.write_text(original)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("must not restore unconditional full-suite gates", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

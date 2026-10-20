# Skill installation checks

`make skills` checks the vendored inventory, licenses, generated manifest and the
external resources listed in `config/skill-install-resources.json`. A matching
upstream folder hash does not prove that referenced files outside that folder or
runtime engines have been installed.

`make skills-runtime` also probes the exact Impeccable engine version named in the
skill's `scripts/VERSION` and checks Fluid Functionalism's local Playwright
package. It is offline and never installs or downloads anything.

## Impeccable engine

The engine is a per-machine cache, not a committed binary. After reviewing the
launcher, run `agents/skills/impeccable/scripts/impeccable engine-probe` from a
network-enabled terminal. The launcher downloads the versioned platform asset,
verifies its SHA-256 sidecar and caches it under `~/.impeccable/bin/<version>/`.
Then run `make skills-runtime`. Windows uses the existing `dot skill-engine -Apply`
and verification-only `dot skill-engine` workflow. Engine installation is separate
from refreshing SKILL.md and the lock record.

## Browser helpers

Fluid Functionalism's audit requires the dependencies declared in its
`scripts/package.json`, installed locally with lifecycle scripts disabled. Its
`node_modules` stays ignored and is not part of the public projection.

Localhost Screenshots uses the target project's Playwright installation. Run its
helpers with cwd at that project and the stable Node executable; follow its pinned
Playwright version and browser setup instructions. The local loader fix is held
against refresh until upstream includes it. Tests prove lookup from an unrelated
project directory without launching a browser.

Python libraries, project frameworks, browser downloads and authenticated service
connections remain task-specific. Use the skill's isolated environment or the
host's bundled runtime where applicable; do not install Python packages globally
or treat missing optional credentials as a broken installation.

## Repository-level references

Six Anthropic skills link to `../../CONNECTORS.md`. The installed
`agents/CONNECTORS.md` combines the upstream engineering and design category
references with a routing introduction; it enables no integrations. Hallmark's
external docs, tokens and worked examples live under `agents/docs/` and
`agents/site/` so its original relative paths resolve. Two supplemental human-doc
links are corrected for this installed layout. Upstream revisions, origins,
checksums and assembly notes are in `config/skill-install-resources.json`.

Keep these supplemental resources when refreshing or projecting the corresponding
skills. Update their source records when their upstream content changes. A skill
installer that copies only the skill directory will not restore these resources.

## Ownership

The shared tree is repository-managed. Paseo's six supported skills now have
GitHub lock records; the retired `paseo-loop` skill and client link rows are removed.
Scheduling and heartbeat functionality remains available through Paseo. Personal
orchestration preferences are retained outside this tree.

Aside's entry point is vendor-CLI-managed; its live guide comes from that CLI.
`code-review-nextjs` is locally authored. Codex system and plugin-cache skills are
owned by Codex/plugin updates and must not be overwritten with shared-tree copies.
The nested `creative/typographic-poster-design` skill is also locally authored;
inventory discovery includes nested tracked skills and excludes dependency trees.

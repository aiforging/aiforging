## What this changes

<!-- One concern per PR. Say what changed in behavior, not just which files moved. -->

## Why

<!-- What problem does this solve? If it's a convention or a pattern, what does it cost? Every
     convention constrains something; if you can't name the cost, it isn't understood yet. -->

## Checklist

- [ ] One concern only
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`
- [ ] If this adds anything the plugin **copies** into a workspace or target repo (a skill, a convention directory, a template, a seeded pattern), it is registered in `.claude-plugin/artifacts.json` — otherwise it installs on fresh setups and silently never reaches existing users
- [ ] Mirrored docs updated together where applicable (`conventions/features/README.md` ↔ `templates/docs-features-README.md`; see `CLAUDE.md`)
- [ ] Scripts smoke-tested under both `uv run` and `python3`, if touched
- [ ] Does not reimplement a `superpowers` skill
- [ ] `PLAN.md` session log updated, if this was a working session on the framework

---
name: architecture-analyzer
description: Use when /aiforging:setup has confirmed a backend or fullstack project and needs a non-destructive, advisory audit of how closely that project's current structure aligns with the AI Forging architectural ideals. Produces a structured ANALYSIS.md report with a score, findings, and severities. Never modifies files.
---

# Architecture Analyzer

## Purpose

Read a target project's current shape and compare it against the AI Forging architectural ideals documented in `${CLAUDE_PLUGIN_ROOT}/conventions/architecture/` and `${CLAUDE_PLUGIN_ROOT}/conventions/tdd/`. Produce a clear, honest report the user can act on.

**This skill is read-only.** It never creates, edits, deletes, or moves files in the target project. If a user asks the skill to "fix" what it found, refer them to the `hammer-refactor` skill (the executable Hammer stage) or to manual refactoring with the pattern library. `/aiforging:execute-plan` remains unshipped.

## When to activate

- Invoked explicitly by `/aiforging:setup` Step 5 against each confirmed backend or fullstack project.
- Invoked directly by a user who wants a standalone audit without re-running setup.

## Inputs

- **Target project root**: absolute path to the project to analyze. Required.
- **Detected ProjectInfo**: the JSON blob from `scripts/detect-project.py`, if already available. If not, the skill runs the detector first.

## Outputs

Write the report to `<target>/.aiforging/ANALYSIS.md`. Also return a concise top-line summary (score + top 3 findings) to the caller for inline display.

The report has this shape:

```markdown
# AI Forging Architecture Analysis

**Project:** <name>
**Path:** <abs path>
**Stack:** <detected stack, e.g., symfony-php + doctrine + phpunit>
**Analyzed:** <ISO date>
**Score:** <0-10>

## Summary

<2-3 sentences on the overall shape. What's healthy, what's not.>

## Findings

<One section per finding, ordered by severity (critical → high → medium → low → info).>

### [<severity>] <Finding title>

**What we saw:**
<Concrete evidence with file paths and line numbers or quoted snippets.>

**Why it matters:**
<One paragraph referencing the relevant AI Forging convention doc.>

**How to fix it:**
<High-level refactor direction. Do NOT write patch/code.>

**Related conventions:**
- `conventions/architecture/<relevant-doc>.md`
- `conventions/refactoring/anti-patterns/<relevant>.md`

## Checklist

<Yes/No table of the capability contract items, see below.>

## Next

The proposed plan for remediation will be written to
`<target>/.aiforging/PROPOSED_PLAN.md` by `/aiforging:setup` Step 6.
```

## Analysis dimensions

For each dimension, collect evidence, determine a rating (healthy / mixed / poor / absent), and translate the rating into findings with severities.

### 1. Domain-centric folder layout

- **Inspect:** Top-level `src/` (or stack-equivalent) tree. Do you see `Domain/Feature/Subfeature/Layer` or something close? Or do you see architecture-centric folders (`Controllers/`, `Services/`, `Repositories/`) at the top of `src/`?
- **Healthy:** Domain-centric layout with Feature boundaries that correspond to business concepts, two levels of nesting, layer folders nested inside feature folders.
- **Mixed:** Hybrid — some features have been migrated, others haven't.
- **Poor:** Architecture-centric layout with some feature grouping inside each layer.
- **Absent:** Pure architecture-centric layout (default framework template).
- **Severity if absent:** High. This is the structural foundation.
- **Reference:** `conventions/architecture/domain-driven-hexagonal.md`

### 2. Single-action controllers

- **Inspect:** Every controller class under the detected controllers directory. Count public methods per class.
- **Healthy:** Every controller has exactly one public entry method (`__invoke` / `handle` / `execute`), and the class name is `<Verb><Noun>Controller`.
- **Mixed:** Some fat controllers remain, some have been split.
- **Poor:** Most controllers have 3+ public methods.
- **Absent:** Default framework CRUD controllers everywhere.
- **Severity if poor/absent:** Medium. Structural but mechanical to fix.
- **Reference:** `conventions/architecture/single-action-controllers.md`, `conventions/refactoring/anti-patterns/fat-controller.md`

### 3. Repository boundaries

- **Inspect:** Services, Controllers, and Entities in the target. Look for direct `EntityManager`, `DataSource`, `DbContext`, or ActiveRecord model usage outside of Repository classes.
- **Healthy:** Services depend on `XxxRepositoryInterface`, implementations are clearly named (`DoctrineXxxRepository`, `TypeOrmXxxRepository`), controllers do not touch persistence at all.
- **Mixed:** Some Services use Repositories, others still hit the EntityManager directly.
- **Poor:** Controllers or Services frequently call ORM APIs directly. Repositories exist but are thin wrappers over `$em->getRepository(...)`.
- **Absent:** No Repository classes; direct ORM usage everywhere.
- **Severity:** High if absent, Medium if poor.
- **Reference:** `conventions/architecture/repositories.md`

### 4. Test harness capability contract

This is the single most important dimension for the Fire stage of the forge.

- **Inspect:** The project's test configuration, base test case, fixtures, and Repository tests.
- **Check each of the five contract items from `conventions/tdd/test-harness-requirements.md`:**
   1. Isolated database per test class (✓ / ✗)
   2. Schema built from the entity graph, not migrations (✓ / ✗)
   3. Fast enough for the Red/Green/Refactor loop (~5s for a feature) (✓ / ✗ / unknown)
   4. Factory-based fixtures, not SQL fixtures (✓ / ✗)
   5. Isolation from developer environment (✓ / ✗)
- **Severity:** Critical if schema-from-metadata is absent. High if fixtures are SQL-based. High if tests share state across classes.
- **Reference:** `conventions/tdd/test-harness-requirements.md`

### 5. DTO and Value Object discipline

- **Inspect:** Service signatures, Entity constructors, and HTTP request/response classes.
- **Healthy:** Domain concepts are represented by Value Objects (`CustomerId`, `Money`, `EmailAddress`). HTTP boundary uses DTOs. Primitives appear only at the boundary.
- **Mixed:** Value Objects exist for the important types but many primitives remain.
- **Poor:** Primitive obsession throughout. `int`, `string`, `float` everywhere.
- **Absent:** No Value Objects at all; anemic Entities with setter/getter pairs.
- **Severity if poor/absent:** Medium.
- **Reference:** `conventions/architecture/dtos-and-value-objects.md`, `conventions/refactoring/anti-patterns/primitive-obsession.md`

### 6. Pattern library presence

- **Inspect:** `.aiforging/refactoring/patterns/` and `.aiforging/refactoring/anti-patterns/` in the target.
- **Healthy:** Both directories exist with at least one file each. (Expected immediately after `/aiforging:setup` installs the starter library.)
- **Absent:** Neither directory exists.
- **Severity:** Info. This is typically a symptom of "setup hasn't been fully installed yet" rather than a deep architectural issue.
- **Reference:** `conventions/refactoring/README.md`

## Scoring

Rough rubric (the analyzer should explain how it arrived at the score, not just emit a number):

| Score | Meaning |
|---|---|
| 9–10 | Already aligned. AI Forging will mostly add the refactor pattern library and reinforcing conventions. |
| 7–8  | Close. A few targeted refactors will bring it into alignment. |
| 5–6  | Mixed. The overall shape is workable but significant dimensions are poor. The proposed plan will be long. |
| 3–4  | Distant. Most dimensions are poor. Adoption is possible but expensive; recommend a phased approach. |
| 0–2  | Incompatible shape. Either the project was scaffolded from a very different template, or AI Forging is a poor fit for this codebase. Discuss with the human partner before proposing a plan. |

Do not claim false precision — if you can't tell whether a dimension is Mixed or Poor, say so. The point is honesty, not a number.

## Severity definitions

| Severity | Meaning |
|---|---|
| **Critical** | The Fire stage of the forge cannot run reliably until this is fixed. Blocks TDD for data-driven code. |
| **High** | Major deviation from architectural ideals. Refactor is worthwhile and likely to reveal latent bugs. |
| **Medium** | Deviation from conventions that's workable but should be fixed before the codebase grows further. |
| **Low** | Cosmetic or naming-only. Fix opportunistically during other refactors. |
| **Info** | Observation, not an action item. |

## How to run

1. If no `ProjectInfo` was passed in, invoke the detector first and parse the JSON. Use the same `uv`-with-`python3`-fallback probe that `/aiforging:setup` uses, because `uv` is not guaranteed to be on PATH:

   ```bash
   if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi
   $FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/detect-project.py <target>
   ```
   The detector script is a PEP 723 single-file script with no third-party deps, so `python3` works identically to `uv run`.
2. Walk the target's `src/` (or stack equivalent) — use `Read`, `Glob`, and `Grep` for everything. Do NOT shell out to write anything.
3. For each of the six dimensions above, gather evidence and decide the rating.
4. Compile findings. Assign severities.
5. Compute the score and write the summary.
6. Write the full report to `<target>/.aiforging/ANALYSIS.md`.
7. Return the top-line summary (score + top 3 findings by severity) to the caller.

## Hard rules

- **Never write to files outside `<target>/.aiforging/ANALYSIS.md`.**
- **Never modify source files.** No "small fixes while I'm in here."
- **Never propose a refactor you haven't evidenced.** Every finding must cite at least one concrete file path or pattern match.
- **Never hide findings to keep the score up.** The point of this analysis is to tell the user the truth.
- **If a dimension cannot be assessed** (e.g., the project has no tests yet), mark it explicitly as "Not assessed" with the reason. Do not guess.

## Related

- `${CLAUDE_PLUGIN_ROOT}/commands/setup.md` — invokes this skill in Step 5.
- `${CLAUDE_PLUGIN_ROOT}/conventions/architecture/`
- `${CLAUDE_PLUGIN_ROOT}/conventions/tdd/`
- `${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/`

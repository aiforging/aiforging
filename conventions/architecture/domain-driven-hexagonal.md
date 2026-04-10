# Domain-Driven Hexagonal Architecture — Folder Layout

## What this is

AI Forging prescribes a domain-centric folder layout inside both `src/` and `tests/`. The top-level organizing concept is the **domain feature**, not the **architectural layer**. You do not have a global `Controllers/` directory. Each feature owns its controllers, services, repositories, entities, value objects, and DTOs, next to each other, in one place.

This is the opposite of the default Symfony/Laravel/Spring project template. Those templates optimize for "where do I put a controller?". We optimize for "everything about feature X lives here." The payoff is that a new contributor reading one feature folder gets the whole story without hopping through seven top-level directories.

## The shape

```
src/
└── Domain/
    ├── Feature1/
    │   ├── Shared/                    ← stuff used by more than one sub-feature
    │   │   ├── Service/
    │   │   ├── Repository/
    │   │   ├── Entity/
    │   │   ├── ValueObject/
    │   │   └── DTO/
    │   ├── Feature1a/
    │   │   ├── Command/               ← CLI entry points, not CQRS-in-the-generic-sense
    │   │   ├── Controller/            ← single-action, HTTP entry points
    │   │   ├── Service/               ← orchestration, business rules
    │   │   ├── Repository/            ← data access, one per aggregate
    │   │   ├── Entity/                ← domain objects (POPOs, POJOs, POCOs)
    │   │   ├── ValueObject/           ← small immutable types
    │   │   └── DTO/                   ← boundary types, not domain types
    │   └── Feature1b/
    │       └── ... same layers ...
    └── Feature2/
        └── ... same shape ...

tests/
└── Domain/
    ├── Feature1/
    │   ├── Feature1a/
    │   │   ├── ControllerTest/        ← or the stack's idiomatic test name
    │   │   ├── ServiceTest/
    │   │   ├── RepositoryTest/        ← hits a real isolated DB. See tdd/repository-testing.md
    │   │   └── EntityTest/
    │   └── Feature1b/
    └── Feature2/
```

The `tests/` tree **mirrors** the `src/` tree. This is not a convention you violate for convenience. One feature folder in `src/`, one feature folder in `tests/`, same name, same depth.

## Why `Shared/` exists

`FeatureN/Shared/` holds anything used by more than one sub-feature under `FeatureN`. It is deliberately narrower than a global `Shared/` or `Common/` directory — sharing is **intra-feature**, not cross-feature. If two features truly need the same thing, that is a sign the concept belongs to a new feature of its own, or it belongs at the `Domain/` root in a small, ruthlessly-reviewed `Common/` package.

Resist the urge to hoist things into a global `Common/`. Hoisted code is how architecture rots.

## Depth is a trade-off

You will be tempted to nest further — `Module/Something/Feature/Something/…`. Don't. Two meaningful levels of nesting (Feature and Subfeature) is the sweet spot. Deeper nesting makes import paths unreadable, makes refactors painful, and almost always encodes an org chart rather than a domain boundary. If you feel the need to nest deeper, first ask whether you actually have two features or one feature with internal sub-modules.

## Namespacing

Namespace/package names follow the folder structure exactly. In a Symfony/PHP project:

```
namespace App\Domain\Billing\Invoicing\Service;
class IssueInvoiceService { ... }
```

In a Spring/Java project:

```
package com.example.domain.billing.invoicing.service;
public class IssueInvoiceService { ... }
```

In a Node/TS project (with path aliases):

```typescript
// src/domain/billing/invoicing/service/issue-invoice.service.ts
export class IssueInvoiceService { ... }
```

The rule is: the folder path **is** the namespace. No shortcuts, no aliases that hide the structure.

## What does NOT go here

- **Global infrastructure code** (database connection factories, HTTP kernel wiring, framework bootstrapping) lives outside `Domain/` in an `Infrastructure/` or framework-idiomatic location.
- **Generic utilities** (date helpers, string helpers) go in an `Infrastructure/` or `Support/` tree. If a utility has any business meaning, it's a ValueObject and it belongs to the feature that owns it.
- **Cross-cutting concerns** (logging adapters, auth middleware, event dispatchers) live in `Infrastructure/` and are wired into the domain via interfaces the domain owns.

## When you're adding a new feature

1. Decide which top-level `Domain/FeatureN/` this belongs under. If it's a new top-level feature, create it.
2. Create `Domain/FeatureN/FeatureNx/` with the layer subfolders you actually need.
3. Do not create empty layer folders you don't yet need — add them as you go.
4. Write the test first in the mirroring `tests/` location.
5. After green, run the post-TDD refactor pass against the changed files.

## Anti-patterns this layout prevents

- The "fat controller" anti-pattern — because controllers are tiny, single-action, and live next to their Service.
- The "god service" anti-pattern — because services are scoped to a sub-feature.
- The "leaky entity" anti-pattern — because DTOs and ValueObjects are right there, screaming to be used at the boundary.
- The "where the hell is this used" anti-pattern — because everything about a feature is in one folder.

## Related conventions

- `architecture/single-action-controllers.md`
- `architecture/repositories.md`
- `architecture/dtos-and-value-objects.md`
- `tdd/repository-testing.md`

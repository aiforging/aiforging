# Test Harness Capability Contract

## Why this file exists

The TDD loop in `fire-red-green-refactor.md` depends on the test suite being **trustworthy, fast, and capable of real database work against a schema built from the entity graph**. Without that, Repository tests collapse into mock-heavy theater, and the rest of the framework loses its spine. This file specifies the contract a test harness must satisfy. Each stack adapter is responsible for showing how that stack satisfies the contract.

## The contract

A conforming test harness MUST provide:

### 1. Isolated database per test class (at minimum)

Each test class runs against its own clean database. Two test classes running in parallel must not see each other's data. The cleanest approaches:

- **Per-class schema**: one database is created, schema is built once, and each test class wraps its work in a transaction that's rolled back at tear-down.
- **Per-class database**: one database per test class, dropped at tear-down. Slower, absolutely deterministic.
- **Per-test transaction inside a per-class database**: the middle ground. Fastest isolation short of full drop.

Pick one, document it, stick to it. Do not mix strategies in the same codebase.

### 2. Schema built from the entity graph, not from migrations

The harness builds the database schema **from the application's entity metadata**, not by running migration files. Why: migrations encode history, including the mistakes you're about to refactor. Tests should see the current shape of your domain, not the accumulated archaeology.

- **Doctrine (Symfony/PHP)**: use `SchemaTool::createSchema($metadata)` where `$metadata` is the full metadata collection from the EntityManager.
- **Hibernate (Spring/Java)**: `hibernate.hbm2ddl.auto=create-drop` on the test profile, or the equivalent `SchemaExport` API.
- **Entity Framework (.NET/C#)**: `Database.EnsureCreated()` with the test `DbContext`.
- **TypeORM (Node/TS)**: `dataSource.synchronize(true)` after initialization.
- **MikroORM (Node/TS)**: `orm.getSchemaGenerator().createSchema()`.
- **Prisma (Node/TS)**: more awkward — migrations are first-class. Use `prisma migrate reset` against a test database, or `prisma db push` with the test schema file.
- **Drizzle (Node/TS)**: `drizzle-kit push` against the test database.
- **Eloquent (Laravel/PHP)**: the ActiveRecord exception. Use migrations + `RefreshDatabase` trait. Not ideal but pragmatic.

### 3. Fast enough to run in the Red/Green/Refactor loop

Target: a feature's Repository test suite should run in under **5 seconds**. Full backend suite in under **60 seconds** on a developer laptop. If you're slower than that, the TDD loop degrades into "write a bunch of code, run tests at lunch." Some ways to get there:

- SQLite in-memory for tests where the schema is simple enough.
- Postgres or MySQL in a container, started once per test run, reused across classes.
- Shared connection pool across test classes.
- Transaction-rollback isolation (as above).

### 4. Deterministic fixtures via factories, not SQL files

- No `.sql` fixture files. They rot, they diverge from the schema, and they hide the meaning of the data behind columns.
- Use factories (`factory-bot`-style) or a fixture builder that constructs Entities via their domain constructors. The factory's job is to produce a valid Entity with sensible defaults and overridable fields.
- A test that sets up state by calling Repository methods (or Entity constructors) is more honest than a test that `INSERT`s rows with magic values.

### 5. Truly isolated from developer environment

- The harness does NOT read the developer's `.env` — it reads a test-specific config (`.env.test`, `phpunit.xml <env>` block, Spring `@TestPropertySource`, etc.).
- The harness does NOT hit external services (Stripe, SendGrid, S3) — it uses fakes, and the fakes live in the test harness itself, not in production code.
- The harness does NOT leave behind test data. Every run starts clean.

## What Claude should verify

When `/aiforging:setup` runs the architecture analyzer, the analyzer reports whether each capability above is satisfied. Findings worth flagging:

- **No schema-from-metadata**: tests rely on migrations or on a pre-seeded database. This is the single most common blocker; prioritize fixing it.
- **Shared test database across classes**: race conditions waiting to happen.
- **Slow Repository tests**: > 10 seconds for a single feature. Diagnose before prescribing refactors that depend on fast tests.
- **Fixture .sql files present**: flag for replacement with factory-based fixtures.
- **Direct external-service calls in tests**: flag as high priority.

## Stack adapter responsibility

Each stack adapter that ships with AI Forging MUST include:

1. A documented setup procedure for the test harness (one page, copy-pasteable config snippets).
2. A smoke-test command that confirms each of the five capabilities above.
3. A sample factory for one Entity, demonstrating the factory pattern in that stack's idiom.
4. A sample Repository test, demonstrating transaction-based isolation and schema-from-metadata.

If a stack cannot satisfy the schema-from-metadata requirement cleanly (looking at you, Prisma and Eloquent), the adapter must document the closest-available workaround and name its trade-offs.

## Related

- `tdd/repository-testing.md`
- `tdd/fire-red-green-refactor.md`
- `architecture/repositories.md`

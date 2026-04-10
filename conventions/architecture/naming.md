# Naming

Naming rules the AI Forging framework enforces. These are intentionally prescriptive. Consistency here pays for itself every time someone (human or AI) navigates the codebase.

## Classes

| Kind | Pattern | Example |
|---|---|---|
| Controller (single-action) | `<Verb><Noun>Controller` | `CreateInvoiceController` |
| Service | `<Verb><Noun>Service` | `CreateInvoiceService` |
| Repository interface | `<Noun>RepositoryInterface` | `InvoiceRepositoryInterface` |
| Repository impl | `<Stack><Noun>Repository` | `DoctrineInvoiceRepository` |
| Entity | `<Noun>` | `Invoice` |
| Value Object | `<Noun>` | `InvoiceId`, `Money` |
| Request DTO | `<Verb><Noun>Request` | `CreateInvoiceRequest` |
| Response DTO | `<Noun>Response` or `<Adjective><Noun>Response` | `InvoiceResponse`, `InvoiceSummaryResponse` |
| CLI Command | `<Verb><Noun>Command` | `IssueMonthlyInvoicesCommand` |
| Exception | `<Noun>Exception` | `InvoiceNotFoundException` |

**Rules behind the rules:**

- Services are named after the **action**, not the noun. `CreateInvoiceService`, not `InvoiceService`. A service with a noun name and no verb will accumulate methods forever — the filesystem stops policing it.
- Controllers mirror the Service name 1:1. If there's a `CreateInvoiceService`, the only controller that calls it is `CreateInvoiceController`. Exceptions only when a single action is reused across multiple HTTP routes (rare).
- Repository interface and implementation class names are different. `InvoiceRepositoryInterface` is what Services depend on. `DoctrineInvoiceRepository` (or `TypeOrmInvoiceRepository`, `HibernateInvoiceRepository`) is what gets wired in. The `Interface` suffix is unfashionable in some languages but eliminates ambiguity.

## Methods

- Services expose one primary public method. Name it after the action itself, or use the language-idiomatic "invoke" form: `__invoke` (PHP), `run` (TS/Node), `execute` (C#/Java). Name it consistently across the codebase.
- Repository methods read like sentences: `findById`, `findUnpaidIssuedSince`, `save`, `delete`. Not `get`, not `fetch`, not `load`.
- Value Object methods describe computation or derivation: `add`, `subtract`, `isZero`, `convertTo`. Not `getValue` — that's what primitives are for, and you shouldn't be reaching for it.
- Boolean methods start with `is`, `has`, or `can`: `isPaid`, `hasOverdueLines`, `canBeCanceled`.

## Files

- One public class per file. Ever. No exceptions for "small helper classes." If the helper is small enough to squeeze into the same file, it's small enough to be a Value Object in its own file.
- File name matches the class name exactly, respecting the language's casing convention.
- Test file names mirror the class name plus a test suffix: `CreateInvoiceServiceTest`, `CreateInvoiceService.test.ts`, `CreateInvoiceServiceTests.cs`.

## Folders

- `PascalCase` for folders in languages where that's idiomatic (PHP/Symfony, C#, Java package-as-folders is lowercase — follow the language, not this rule). For Node/TS projects use `kebab-case` consistently.
- Folder names are singular: `Controller/`, `Service/`, `Repository/`, `Entity/`, `ValueObject/`, `DTO/`. The folder holds "a bunch of Controllers" but its name is singular. This matches the language convention of "type category."

## Variables and parameters

- No Hungarian notation. No `strName`, no `intCount`.
- Prefer meaningful over short: `customerId` over `cid`, `issuedAt` over `dt`.
- Loops: `foreach ($invoices as $invoice)` — the variable name reads like English.
- Do not name variables after their type unless the type itself is the meaning: `Money $amount` is fine; `Money $money` is not.

## Avoid

- `Manager`, `Helper`, `Handler`, `Processor`, `Utility` in class names. These are the big four suffixes of "I couldn't think of what this class does." If you reach for one, stop and describe the actual action.
- `Impl` suffixes on implementation classes (use `Doctrine`, `TypeOrm`, `Http`, `InMemory` prefixes or stack-specific prefixes instead).
- Pluralized type names: `Invoices` is not a class. If you need a collection type, name it `InvoiceCollection`.
- Abbreviations that aren't globally understood. `Cust` is not `Customer`. `Inv` could mean `Invoice` or `Inventory` or `Investment`. Spell it out.

## Related

- `architecture/single-action-controllers.md`
- `architecture/repositories.md`
- `architecture/dtos-and-value-objects.md`

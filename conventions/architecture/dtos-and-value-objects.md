# DTOs and Value Objects

## The distinction

Both are small, mostly-immutable, primitive-wrapping classes. They are not the same thing and they do not live in the same folder.

**Value Object**: a domain concept with identity-by-value. `Money(1000, 'USD')` equals another `Money(1000, 'USD')`. `EmailAddress('foo@example.com')` enforces the "this string is a valid email" invariant in its constructor. Value Objects belong to the **domain** — they live next to Entities and Services.

**DTO**: a boundary type. It crosses a layer edge — HTTP request body → Service input, Service output → HTTP response, API call → external service, CLI argv → Command input. DTOs have no behavior. DTOs have no invariants beyond "these fields are present and well-typed." DTOs are not used *inside* domain logic; they are consumed at the edge and translated into Value Objects and Entity arguments.

Violate this distinction and you get either (a) anemic domain objects with no behavior, because everything's a DTO; or (b) DTOs that creep into your Services and leak your HTTP shape into your business logic.

## Where they live

Inside each feature folder:

```
src/Domain/Billing/Invoicing/
├── ValueObject/
│   ├── InvoiceId.php
│   ├── InvoiceNumber.php
│   ├── Money.php
│   └── TaxRate.php
└── DTO/
    ├── CreateInvoiceRequest.php          ← HTTP input
    ├── CreateInvoiceResponse.php         ← HTTP output
    └── InvoiceSummaryDTO.php             ← read-model for list endpoints
```

## Value Object rules

- **Constructor enforces invariants.** `new EmailAddress('nope')` throws. `new Money(-5, 'USD')` throws if negative amounts aren't allowed. There is no "validate later" method.
- **Immutable.** No setters. "Changing" a Value Object returns a new one: `$newMoney = $money->add(new Money(500, 'USD'));`.
- **Equality by value, not reference.** Implement `equals()` if your language doesn't give it for free.
- **Has behavior.** `Money` adds, subtracts, converts. `EmailAddress` has `domain()`. If your Value Object is just a dumb primitive wrapper with no methods, it's a missed opportunity.
- **Doesn't know about persistence.** No ORM annotations unless your ORM requires embedded-value annotations. Even then, keep the annotation minimal and the class pure.

## DTO rules

- **Immutable after construction.** Readonly properties / `final class` / `Record` / whatever your language gives you.
- **No domain invariants.** A DTO doesn't reject a negative invoice amount. That check happens when the Service builds the Entity from the DTO. DTOs only enforce shape — types and presence.
- **No dependencies.** No repository, no service, no framework objects. A DTO is a bag of fields.
- **No inheritance.** Flat classes. If two DTOs share fields, that's a coincidence, not a hierarchy.
- **One-way.** A DTO either goes into the domain (request DTO) or comes out of it (response DTO). Don't reuse the same class for both directions.

## Primitives at the edges, Value Objects at the core

The rule: **primitives crossing the boundary, Value Objects inside**.

```
HTTP request (JSON)
   ↓
CreateInvoiceRequest DTO { customerId: string, amountCents: int, currency: string }
   ↓
CreateInvoiceService runs:
   $customerId = new CustomerId($request->customerId);
   $amount     = new Money($request->amountCents, $request->currency);
   $invoice    = Invoice::issue($customerId, $amount);   ← domain, all Value Objects
   ↓
InvoiceRepository->save($invoice)
   ↓
Return InvoiceResponseDTO with primitives
   ↓
HTTP response (JSON)
```

The Service is the only place that knows how to convert between the boundary representation and the domain representation. Controllers don't build Value Objects. Repositories don't return DTOs.

## Naming

- Value Objects: `InvoiceId`, `Money`, `TaxRate`, `EmailAddress`, `PostalCode`. Nouns. No suffix.
- Request DTOs: `CreateInvoiceRequest`, `UpdateInvoiceRequest`. Named after the action.
- Response DTOs: `InvoiceResponse`, `InvoiceSummaryResponse`. Named after what they describe, with the `Response` suffix.
- Internal DTOs: `InvoiceSummaryDTO`, `MonthlyRevenueReport`. The `DTO` suffix is fine for things that cross layer edges *inside* the backend (e.g., a read-model from a Repository to a Service to a Presenter). Avoid it for HTTP boundary classes — `Request`/`Response` is clearer.

## Anti-patterns this prevents

- **Primitive obsession.** `createInvoice(int $customerId, int $cents, string $currency)` becomes `createInvoice(CustomerId $customerId, Money $amount)` — and the compiler catches parameter-order mistakes that used to be silent bugs.
- **Anemic domain model.** Pushing all the logic into Services because Entities are "just data" is a smell. Value Objects are where the "where does this logic go?" pressure gets relieved.
- **Leaky HTTP shape.** Passing the HTTP request object all the way into the Service means every Service knows about HTTP. DTOs stop that.

## Related

- `architecture/domain-driven-hexagonal.md`
- `architecture/repositories.md`
- `refactoring/anti-patterns/primitive-obsession.md`
- `refactoring/anti-patterns/anemic-domain-model.md`

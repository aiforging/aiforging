---
applies-to: [all]
seeded: true
---

# Primitive Obsession

## Rule

Domain concepts with invariants must be represented by Value Objects, not by bare primitives (`string`, `int`, `float`, `DateTimeImmutable`, etc.). Method parameters, Entity properties, and return types should use the Value Object whenever the primitive has meaning beyond its raw type.

## Why

Primitives cross the boundary at the edge of the system (HTTP, CLI, external API). Once inside the domain, they should become typed Value Objects. This catches:

1. **Parameter-order bugs.** `createInvoice(int $customerId, int $amountCents)` vs. `createInvoice(CustomerId $customerId, Money $amount)` — the compiler stops you from passing them in the wrong order.
2. **Validation drift.** When "customer ID must be a positive integer" is a rule, the rule should live in `CustomerId`'s constructor, once. When every function that takes a customer ID has to check, the rule rots.
3. **Lost meaning.** `float $tax` could be a tax rate, a tax amount, a tax-inclusive total, or a tax-excluded subtotal. `TaxRate`, `Money`, `GrossAmount`, `NetAmount` are obvious.
4. **Poor discoverability.** IDEs and type checkers can't suggest `$money->add($other)` if `$money` is a `float`.

See `architecture/dtos-and-value-objects.md` for the Value Object rules.

## Detect

Mechanical signals a subagent can check in the session's changed files:

1. **Method parameters with primitive types and domain-ish names.** `int $customerId`, `string $email`, `int $amountCents`, `float $taxRate`, `string $invoiceNumber`. The name tells you the primitive is carrying meaning the type doesn't capture.
2. **Entity properties typed as primitives for domain concepts.** Look at each `Entity/` class — any `string $email`, `int $customerId`, `float $amount` in a constructor signature is suspect.
3. **Repeated validation.** The same `if ($email !== null && filter_var($email, FILTER_VALIDATE_EMAIL))` check appearing in more than one Service is a screaming signal the validation should have moved into `EmailAddress`.
4. **Money or currency handled as `float`.** This is always wrong. Always. Floats do not represent money. If you see `float $amount`, flag it immediately.
5. **Date logic on bare `DateTimeImmutable`.** "Issued more than 30 days ago" computed inline with `diff()->days` instead of a `BillingPeriod` or `InvoiceAge` Value Object.

## Eliminate

1. Identify the primitive and the concept it's carrying.
2. Create a Value Object in the feature's `ValueObject/` folder. Give it a constructor that enforces the invariants. Give it `equals()` and any obvious behavior methods.
3. Update the Entity, Service, and Repository signatures to use the Value Object.
4. Update tests. This is usually where you discover whether your test harness was relying on the primitive representation — if a test was passing `42` where it should have been `new CustomerId(42)`, that's fine; the fix is trivial.
5. At the HTTP/CLI boundary (DTOs), keep the primitives. The Service's job is to translate from the primitive DTO to the Value Object when it builds the Entity.
6. Run the full test suite. If any test breaks, investigate — primitive-obsession fixes have a high rate of exposing latent bugs.

### Before

```php
final class CreateInvoiceService
{
    public function __construct(
        private InvoiceRepositoryInterface $invoices,
        private CustomerRepositoryInterface $customers,
    ) {}

    public function run(int $customerId, int $amountCents, string $currency): Invoice
    {
        if ($amountCents <= 0) {
            throw new \InvalidArgumentException('amount must be positive');
        }
        if (!in_array($currency, ['USD', 'EUR', 'GBP'], true)) {
            throw new \InvalidArgumentException('unknown currency');
        }
        $customer = $this->customers->findById($customerId);
        if ($customer === null) {
            throw new CustomerNotFoundException($customerId);
        }
        $invoice = new Invoice($customer, $amountCents, $currency);
        $this->invoices->save($invoice);
        return $invoice;
    }
}
```

### After

```php
final class CreateInvoiceService
{
    public function __construct(
        private InvoiceRepositoryInterface $invoices,
        private CustomerRepositoryInterface $customers,
    ) {}

    public function __invoke(CreateInvoiceRequest $request): Invoice
    {
        $customerId = new CustomerId($request->customerId);
        $amount     = new Money($request->amountCents, Currency::fromIso($request->currency));

        $customer = $this->customers->findById($customerId)
            ?? throw new CustomerNotFoundException($customerId);

        $invoice = Invoice::issue($customer, $amount);
        $this->invoices->save($invoice);

        return $invoice;
    }
}
```

The validation has moved into `Money`, `Currency`, and `CustomerId` constructors. The Service is shorter, clearer, and harder to misuse.

## Don't apply when

- **Generic utility code.** A function that converts any `int` to a zero-padded string doesn't need an `UnpaddedInt` Value Object. Keep utilities generic.
- **The primitive really is the meaning.** An HTTP status code is genuinely just an `int`. A file offset is genuinely just an `int`. Don't Value-Object-ify things that aren't domain concepts.
- **Crossing layer boundaries.** DTOs at the HTTP edge stay primitive. The translation happens in the Service.

## Related

- `architecture/dtos-and-value-objects.md`
- `anti-patterns/anemic-domain-model.md` (stub — add when you write it)

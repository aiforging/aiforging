# Extract Service From Controller

## Rule

Business logic, persistence, orchestration, and cross-collaborator coordination live in a Service class named after the action. Controllers only validate input (via DTO), call one Service method, and serialize the result.

## Why

Controllers belong to the HTTP framework. Services belong to the domain. Mixing them is the fast path to a codebase where every test needs an HTTP kernel and every behavior change ripples through the routing layer. See `architecture/single-action-controllers.md`.

## Detect

Look for controllers that:

1. Call a Repository or ORM directly (`$this->em->...`, `Model::...`, `dbContext.Set<...>`).
2. Contain an `if` branch that represents a business rule ("if the customer is a VIP, apply a discount", "if the invoice is already paid, refuse the update").
3. Coordinate between more than one Service or Repository inside a single method body.
4. Throw domain exceptions directly (`throw new CustomerNotFoundException(...)` belongs in a Service, not a Controller).
5. Have any method longer than ~30 lines.

Any one of these triggers the pattern.

## Apply

1. Decide on the action name. Use the convention `<Verb><Noun>` — e.g., `CreateInvoice`, `CancelInvoice`, `ListUnpaidInvoicesForCustomer`.
2. Create `<Feature>/Service/<Action>Service.php` (or the language equivalent). Give it an injectable constructor for any Repository or collaborator it needs.
3. Move the body of the controller method into a new public method on the Service. Use `__invoke` (PHP), `handle` / `run` (Node), `execute` (Java/C#) as the single entry name. Be consistent across the codebase.
4. Replace any primitives the controller was passing around with Value Objects at the Service boundary where appropriate (see `anti-patterns/primitive-obsession.md`).
5. In the controller, inject the new Service, call its single method, wrap the result in the HTTP response.
6. Write or update a Service test that drives the behavior. This test should not spin up an HTTP kernel — it should exercise the Service directly with the real Repository from the test harness.
7. Run the test suite. Keep green.

### Before

```php
#[Route('/api/invoices', methods: ['POST'])]
final class CreateInvoiceController
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        $data = json_decode($request->getContent(), true);
        $customer = $this->em->find(Customer::class, $data['customerId']);
        if (!$customer) {
            return new JsonResponse(['error' => 'customer not found'], 404);
        }
        if ($customer->isVip()) {
            $data['amount'] = (int) ($data['amount'] * 0.9);
        }
        $invoice = new Invoice($customer, $data['amount']);
        $this->em->persist($invoice);
        $this->em->flush();
        return new JsonResponse($invoice, 201);
    }
}
```

### After

```php
// src/Domain/Billing/Invoicing/Service/CreateInvoiceService.php
final class CreateInvoiceService
{
    public function __construct(
        private readonly CustomerRepositoryInterface $customers,
        private readonly InvoiceRepositoryInterface $invoices,
    ) {}

    public function __invoke(CreateInvoiceRequest $request): Invoice
    {
        $customer = $this->customers->findById(new CustomerId($request->customerId))
            ?? throw new CustomerNotFoundException($request->customerId);

        $amount = new Money($request->amountCents, Currency::fromIso($request->currency));
        $invoice = Invoice::issueFor($customer, $amount);

        $this->invoices->save($invoice);

        return $invoice;
    }
}
```

```php
// src/Domain/Billing/Invoicing/Controller/CreateInvoiceController.php
#[Route('/api/invoices', methods: ['POST'])]
final class CreateInvoiceController
{
    public function __construct(
        private readonly CreateInvoiceService $createInvoice,
    ) {}

    public function __invoke(
        #[MapRequestPayload] CreateInvoiceRequest $request,
    ): JsonResponse {
        $invoice = ($this->createInvoice)($request);
        return new JsonResponse($invoice, 201);
    }
}
```

The VIP discount rule doesn't belong in either the Service OR the Controller — it belongs on `Customer` or on a pricing Value Object. Extract it further if the test suite allows. The Service test can now exercise "VIP customer gets a discount" without touching HTTP.

## Don't apply when

- The endpoint is truly trivial — a health check, a static feature flag, a version endpoint. Extracting a Service for `return ['status' => 'ok']` is overkill.
- The action is a pass-through to an existing Service that already has the right shape. Don't create a wrapper Service for no reason.

## Related

- `architecture/single-action-controllers.md`
- `architecture/domain-driven-hexagonal.md`
- `anti-patterns/fat-controller.md`
- `anti-patterns/primitive-obsession.md`

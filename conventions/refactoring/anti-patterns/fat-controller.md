---
applies-to: [symfony-php, laravel-php, spring-java, dotnet-csharp, ruby-on-rails, node-ts, node-js]
seeded: true
---

# Fat Controller

## Rule

Controllers must be single-action. One public entry method (`__invoke`, `handle`, framework-idiomatic), no business logic, no direct repository or persistence calls.

## Why

The fat controller is the most common architectural smell in web backends. It starts as "just a few lines in the route handler" and ends as a 600-line class that contains validation, business rules, persistence, logging, and error mapping all tangled together. Once a controller is fat it is almost impossible to test cleanly — every assertion has to mock half the world.

The single-action controller is the architectural answer. See `architecture/single-action-controllers.md` for the full rule.

## Detect

A controller class is "fat" if any of the following apply:

1. **More than one public method.** `index()`, `show()`, `create()`, `update()`, `delete()` all on the same class. (Method names like `__invoke`, `handle`, `execute` are the allowed single-entry names.)
2. **Direct repository / EntityManager / DbContext / DataSource access.** The controller calls `$this->em->persist(...)`, `InvoiceModel::create(...)`, `dbContext.Set<Invoice>().Add(...)`, or equivalent. Persistence belongs in a Service via a Repository.
3. **Business rules inside the method body.** "If the customer is a VIP, apply a discount" — that belongs in a Service (or, better, on an Entity).
4. **More than ~30 lines in the entry method.** A single-action controller that exceeds ~30 lines is almost always doing one of the above.
5. **Multiple Services injected without a clear orchestration intent.** If the controller is injecting four Services and coordinating between them, the orchestration belongs in a new Service that coordinates the four.

## Eliminate

1. Identify the actions the fat controller handles. There are usually 3–7 distinct actions (list, show, create, update, delete, plus feature-specific ones).
2. For each action, create a new single-action controller class in the feature's `Controller/` folder. Copy the current action method into `__invoke`.
3. For each action, create a corresponding Service class in `Service/`. Move the business logic and persistence calls from the controller into the Service.
4. Wire each new controller to its route. For Symfony, the `#[Route]` attribute moves to the new class. For Laravel, update `routes/web.php` or `routes/api.php` to bind the class directly. For NestJS, each new controller has its own `@Controller`.
5. Run the test suite after each extraction. If tests break, figure out why before moving on. If a controller's logic wasn't covered by a test, write one before extracting (this is Fire stage).
6. Delete the old fat controller once every action has been moved and the test suite is green.

### Before

```php
#[Route('/invoices', name: 'invoices_')]
class InvoiceController
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    #[Route('', methods: ['GET'])]
    public function index(): JsonResponse
    {
        $invoices = $this->em->getRepository(Invoice::class)->findAll();
        return new JsonResponse($invoices);
    }

    #[Route('', methods: ['POST'])]
    public function create(Request $request): JsonResponse
    {
        $data = json_decode($request->getContent(), true);
        if (empty($data['customerId'])) {
            return new JsonResponse(['error' => 'customerId required'], 400);
        }
        $customer = $this->em->find(Customer::class, $data['customerId']);
        if ($customer->isVip()) {
            $data['amount'] *= 0.9;
        }
        $invoice = new Invoice($customer, $data['amount']);
        $this->em->persist($invoice);
        $this->em->flush();
        return new JsonResponse($invoice, 201);
    }

    // ... show, update, delete, each with their own tangle ...
}
```

### After

```php
// src/Domain/Billing/Invoicing/Controller/ListInvoicesController.php
#[Route('/invoices', methods: ['GET'])]
final class ListInvoicesController
{
    public function __construct(private readonly ListInvoicesService $listInvoices) {}

    public function __invoke(): JsonResponse
    {
        return new JsonResponse(($this->listInvoices)());
    }
}

// src/Domain/Billing/Invoicing/Controller/CreateInvoiceController.php
#[Route('/invoices', methods: ['POST'])]
final class CreateInvoiceController
{
    public function __construct(private readonly CreateInvoiceService $createInvoice) {}

    public function __invoke(#[MapRequestPayload] CreateInvoiceRequest $request): JsonResponse
    {
        return new JsonResponse(($this->createInvoice)($request), 201);
    }
}
```

The VIP-discount rule moves into `CreateInvoiceService` where it can be tested in isolation without touching HTTP.

## Don't apply when

- The "controller" is actually a tiny CLI command with no HTTP surface and no realistic path to growing horns. Pragmatism wins over purity for one-shot scripts.
- A framework's generated admin panel (Symfony EasyAdmin, Rails scaffolded admin, Laravel Nova) is doing CRUD on an internal tool and isn't part of the domain. Leave it alone; it's generated code, not your code.

## Related

- `architecture/single-action-controllers.md`
- `architecture/domain-driven-hexagonal.md`
- `patterns/extract-service-from-controller.md` (stub — add when you write it)

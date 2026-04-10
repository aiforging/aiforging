# Single-Action Controllers

## Rule

Every HTTP controller has exactly one public method. That method is named `__invoke` (PHP), `handle` (Java/TS), or the framework's idiomatic single-entry name. The class is named after the action, not the resource.

Not this:

```php
// src/Controller/InvoiceController.php — DON'T
class InvoiceController
{
    public function list() { ... }
    public function create() { ... }
    public function show(int $id) { ... }
    public function update(int $id) { ... }
    public function delete(int $id) { ... }
}
```

This:

```
src/Domain/Billing/Invoicing/Controller/
├── ListInvoicesController.php
├── CreateInvoiceController.php
├── ShowInvoiceController.php
├── UpdateInvoiceController.php
└── DeleteInvoiceController.php
```

Each file has one class. Each class has one `__invoke`.

## Why

1. **Single Responsibility Principle, enforced by the filesystem.** A class with one method cannot grow horns. It stays tiny or it gets refactored.
2. **Clearer diffs.** A change to "create invoice" touches one file. A change to "show invoice" touches a different file. Reviewers see exactly what changed.
3. **Trivially testable.** One entry point, one set of inputs, one set of outputs. Nothing to mock away that "belongs to another action."
4. **Easy to compose.** If two actions share logic, they share it via a Service, not via a protected method in a shared base controller.
5. **Routing becomes declarative.** You bind a route to a class, not to a class-plus-method. No more hunting for which method handles which verb.

## What goes inside `__invoke`

As little as possible. A controller's job is:

1. Validate the request (via DTO, form, or framework validator).
2. Call one Service method.
3. Serialize the result into an HTTP response.

That's it. No business rules. No repository calls directly from the controller. No side effects. If you find yourself writing a second private method inside the controller, ask whether that method belongs on a Service.

## What it looks like in Symfony/PHP

```php
<?php

declare(strict_types=1);

namespace App\Domain\Billing\Invoicing\Controller;

use App\Domain\Billing\Invoicing\DTO\CreateInvoiceRequest;
use App\Domain\Billing\Invoicing\Service\CreateInvoiceService;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;

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

Notice what is **not** there: no try/catch, no logging, no repository call, no entity construction. Those belong in the Service or in a framework-level exception listener.

## What it looks like in Node/TS (NestJS)

```typescript
// src/domain/billing/invoicing/controller/create-invoice.controller.ts
import { Body, Controller, Post } from '@nestjs/common';
import { CreateInvoiceService } from '../service/create-invoice.service';
import { CreateInvoiceRequest } from '../dto/create-invoice.request';

@Controller('invoices')
export class CreateInvoiceController {
  constructor(private readonly createInvoice: CreateInvoiceService) {}

  @Post()
  async handle(@Body() request: CreateInvoiceRequest) {
    return this.createInvoice.run(request);
  }
}
```

One class, one method, one Service dependency. Same shape, different language.

## How routes wire up

- **Symfony**: `#[Route(...)]` attribute on the class.
- **Laravel**: `Route::post('/invoices', CreateInvoiceController::class);` — Laravel invokes the `__invoke` method automatically when you bind a class instead of a closure or `[Class::class, 'method']` pair.
- **NestJS**: one `@Controller` decorator per file, one HTTP-verb decorator on the single method.
- **Spring**: one `@RestController` class per action with a single `@RequestMapping`-annotated method.
- **ASP.NET**: one controller class, one action method, route via `[HttpPost]` + `[Route]`.

## Common objections

- **"I'll have hundreds of controller files."** Yes. That's fine. Each one will be 20 lines. The filesystem is a much better organizing principle than a 900-line `InvoiceController`.
- **"Shared setup / middleware / auth."** That's what middleware, filters, attributes, and decorators are for. Move it out of the controller entirely.
- **"But the framework's generator creates multi-action controllers."** Ignore the generator. Or replace it with one that produces single-action controllers.

## Anti-pattern this prevents

See `refactoring/anti-patterns/fat-controller.md`.

# Repositories

## Rule

A Repository is a **class**, separate from the Entity it persists, whose job is to speak to the datastore and return domain objects (Entities or Value Objects) — never rows, never arrays of primitives, never framework-specific query builders. Services depend on Repositories via the Repository's own interface, not via the framework's generic `EntityManager` / `DataSource` / `DbContext`.

We prescribe the **Data Mapper** pattern. Entities do not know how they're persisted. Entities do not have static `::find()` methods. Entities do not extend a framework base class. If your framework defaults to Active Record (Eloquent, Rails), you can still follow this pattern — see "Active Record escape hatch" below.

## Why

1. **You can test-drive data access.** A Repository is a plain class with a clear contract. A `find(Id)` method is easy to write a test for. A `static findOrFail(id)` method scattered through a controller is not.
2. **Domain stays pure.** When Entities are POPOs/POJOs/POCOs, your domain logic runs without a database, without a framework, in a unit test, in your head.
3. **Query complexity has a home.** The inevitable "give me all unpaid invoices issued in the last 30 days for customers in Region X" query lives in a Repository method with a name, not inlined into a controller or service.
4. **Mockability is cheap when you need it** (rare — prefer real-DB tests, see `tdd/repository-testing.md`).

## The shape

One interface, one implementation, both inside the feature folder:

```
src/Domain/Billing/Invoicing/Repository/
├── InvoiceRepositoryInterface.php
└── DoctrineInvoiceRepository.php      ← or whatever implementation you have
```

Services depend on the interface. Framework wiring picks the implementation.

```php
<?php

namespace App\Domain\Billing\Invoicing\Repository;

use App\Domain\Billing\Invoicing\Entity\Invoice;
use App\Domain\Billing\Invoicing\ValueObject\InvoiceId;

interface InvoiceRepositoryInterface
{
    public function findById(InvoiceId $id): ?Invoice;

    public function save(Invoice $invoice): void;

    /** @return Invoice[] */
    public function findUnpaidIssuedSince(\DateTimeImmutable $since): array;
}
```

```php
<?php

namespace App\Domain\Billing\Invoicing\Repository;

use App\Domain\Billing\Invoicing\Entity\Invoice;
use App\Domain\Billing\Invoicing\ValueObject\InvoiceId;
use Doctrine\ORM\EntityManagerInterface;

final class DoctrineInvoiceRepository implements InvoiceRepositoryInterface
{
    public function __construct(
        private readonly EntityManagerInterface $em,
    ) {}

    public function findById(InvoiceId $id): ?Invoice
    {
        return $this->em->find(Invoice::class, $id->value);
    }

    public function save(Invoice $invoice): void
    {
        $this->em->persist($invoice);
        $this->em->flush();
    }

    public function findUnpaidIssuedSince(\DateTimeImmutable $since): array
    {
        return $this->em->createQuery(
            'SELECT i FROM ' . Invoice::class . ' i
             WHERE i.paidAt IS NULL AND i.issuedAt >= :since'
        )->setParameter('since', $since)->getResult();
    }
}
```

## Do-not list

- **Do not extend the framework's default repository base class.** That's how you accidentally expose `->createQueryBuilder()` to the rest of the app.
- **Do not return arrays, rows, or DTOs from a Repository.** Repositories return Entities (or a collection of Entities). Mapping to DTOs happens in the Service or a dedicated Mapper.
- **Do not put Repository methods on the Entity.** `Invoice::findAllForCustomer($id)` is a red flag, every time.
- **Do not inject the `EntityManager` / `DataSource` into Services.** Services depend on Repository interfaces. If a Service touches the `EntityManager` directly, it's doing the Repository's job.
- **Do not write one huge Repository per Aggregate with 40 methods.** If a Repository has more than ~8 methods it's trying to own too much. Split by query intent or by sub-aggregate.

## One Repository per Aggregate

You get one Repository per Aggregate Root, not one per Entity. An `Invoice` Aggregate with `InvoiceLine` children gets exactly one `InvoiceRepository`. You do not add an `InvoiceLineRepository`. Lines are loaded and saved through the Invoice.

## Active Record escape hatch (Laravel / Rails)

If your stack defaults to Active Record and you can't migrate away from it cleanly, the Repository pattern still applies — you just wrap your Active Record model behind a Repository interface. The Repository becomes the only place that calls `Model::query()`, `Model::find()`, `::save()`, and so on. Services still depend on the Repository interface, not the Model.

This is less elegant than Data Mapper, but it preserves the important property: **Services and Controllers never touch the database directly**, and tests can swap in a test implementation or exercise a real one.

## Related conventions

- `architecture/domain-driven-hexagonal.md`
- `architecture/dtos-and-value-objects.md`
- `tdd/repository-testing.md`
- `tdd/test-harness-requirements.md`

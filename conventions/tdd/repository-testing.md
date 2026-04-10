# Testing Repositories Against a Real Isolated Database

## The short version

Repository tests hit a real database. Not a mock. Not an in-memory fake that pretends to be your database. **The same database engine you use in production, or as close to it as you can get, running in isolation inside the test harness described in `test-harness-requirements.md`.**

Mocking a Repository's database dependencies makes the test worthless for its actual job — verifying that your query logic and your ORM mapping produce the results you think they do. The bugs that hide in query logic (incorrect joins, wrong grouping, time-zone edge cases, null handling) never surface in a mocked test. They surface in production.

## What a good Repository test looks like

```php
<?php

declare(strict_types=1);

namespace App\Tests\Domain\Billing\Invoicing\Repository;

use App\Domain\Billing\Invoicing\Entity\Invoice;
use App\Domain\Billing\Invoicing\Factory\InvoiceFactory;
use App\Domain\Billing\Invoicing\Repository\InvoiceRepositoryInterface;
use App\Domain\Billing\Invoicing\ValueObject\InvoiceId;
use App\Tests\Support\RepositoryTestCase;

final class DoctrineInvoiceRepositoryTest extends RepositoryTestCase
{
    private InvoiceRepositoryInterface $repo;

    protected function setUp(): void
    {
        parent::setUp();
        $this->repo = $this->container->get(InvoiceRepositoryInterface::class);
    }

    public function test_it_persists_and_finds_an_invoice(): void
    {
        $invoice = InvoiceFactory::any()->build();

        $this->repo->save($invoice);
        $this->em->clear();  // drop the identity map; force a real read

        $found = $this->repo->findById($invoice->id());

        $this->assertNotNull($found);
        $this->assertEquals($invoice->id(), $found->id());
        $this->assertTrue($found->amount()->equals($invoice->amount()));
    }

    public function test_it_finds_unpaid_invoices_issued_after_a_given_date(): void
    {
        $old   = InvoiceFactory::any()->issuedAt('2025-01-01')->unpaid()->build();
        $new1  = InvoiceFactory::any()->issuedAt('2026-04-01')->unpaid()->build();
        $new2  = InvoiceFactory::any()->issuedAt('2026-04-05')->paid()->build();

        $this->repo->save($old);
        $this->repo->save($new1);
        $this->repo->save($new2);
        $this->em->clear();

        $results = $this->repo->findUnpaidIssuedSince(new \DateTimeImmutable('2026-03-01'));

        $this->assertCount(1, $results);
        $this->assertEquals($new1->id(), $results[0]->id());
    }
}
```

What's important here:

1. **`RepositoryTestCase` is a harness-provided base.** It sets up the isolated database, wraps each test in a transaction, exposes the EntityManager, and rolls back on tear-down. You do not reinvent this per test.
2. **`InvoiceFactory::any()->build()` produces a valid Entity.** Not a SQL insert. The factory calls the domain constructor so the Entity is built the way production code would build it.
3. **`$this->em->clear()` is called between `save` and the read under test.** Without it, the ORM's identity map returns the same object instance, and the test never exercises the SELECT. This catches a surprising number of mapping bugs.
4. **The assertion talks about domain objects, not rows.** `$found->amount()` is a Value Object; `equals()` is a domain-level comparison. The test doesn't care about column names.

## What a bad Repository test looks like

```php
// DON'T
public function test_it_finds_an_invoice(): void
{
    $em = $this->createMock(EntityManagerInterface::class);
    $em->expects($this->once())
       ->method('find')
       ->with(Invoice::class, 42)
       ->willReturn(new Invoice(...));

    $repo = new DoctrineInvoiceRepository($em);
    $result = $repo->findById(new InvoiceId(42));

    $this->assertNotNull($result);
}
```

This tests nothing except "my mock was configured to return a value." It verifies no SQL, no schema, no mapping, no query logic. The test would still pass if the actual production query was `SELECT * FROM invoices WHERE id = 'banana'`.

## Patterns you'll use repeatedly

### Transaction-based isolation

The cheapest way to keep tests isolated without per-test database drops:

```php
// RepositoryTestCase::setUp
$this->em->beginTransaction();

// RepositoryTestCase::tearDown
$this->em->rollBack();
```

Everything the test does inside `setUp`/`tearDown` is rolled back. Identity maps and caches are cleared. Next test starts with a clean slate. The schema is built *once* per test run, not per test.

Watch out for tests that intentionally test commit/rollback behavior — those need a different strategy (usually a per-test database).

### Building across multiple saves

When a test needs several related records, call the factory as many times as needed. Factories compose:

```php
$customer = CustomerFactory::any()->build();
$invoice1 = InvoiceFactory::forCustomer($customer)->issuedAt('2026-04-01')->build();
$invoice2 = InvoiceFactory::forCustomer($customer)->issuedAt('2026-04-15')->build();

$this->customers->save($customer);
$this->invoices->save($invoice1);
$this->invoices->save($invoice2);
$this->em->clear();
```

### Asserting counts before details

Before asserting "the result contains invoice X," assert that it has the right count. A test that says `$this->assertEquals($id, $results[0]->id())` without first asserting `count === 1` will silently pass when the query returns 12 invoices and the first one is right by accident.

### Naming convention for test methods

`test_it_<behavior>_<qualifier>`. Examples:

- `test_it_persists_and_finds_an_invoice`
- `test_it_returns_null_when_no_invoice_matches`
- `test_it_ignores_deleted_invoices_in_queries`
- `test_it_rolls_back_partial_saves_on_constraint_violation`

## Repository tests are not Service tests

Repository tests verify persistence and queries. They do not verify business rules. If a business rule lives on the Entity or in a Service, it gets its own test at that level — often without a database at all.

A good Repository test for `findUnpaidIssuedSince` asks "does the query correctly filter by unpaid and by date?". A good Service test for `CancelInvoice` asks "does it refuse to cancel an already-paid invoice?". These are different questions, in different files, at different layers.

## When to mock anyway

The only time a Repository test should use a mock: when the thing being mocked is **not the database**, but rather a genuinely external collaborator (an HTTP client, a message bus, a file storage adapter). Mock those at the edge of the Repository. Keep the database real.

## Related

- `tdd/test-harness-requirements.md`
- `tdd/fire-red-green-refactor.md`
- `architecture/repositories.md`

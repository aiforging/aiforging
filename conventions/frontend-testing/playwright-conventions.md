# Playwright Conventions

## Scope

This document describes how to structure Playwright integration tests for a frontend project that talks to an AI Forging backend. Use it when you've opted into the frontend testing layer during `/aiforging:setup`.

## Layout

```
<frontend-project>/
└── e2e/
    ├── playwright.config.ts
    ├── fixtures/
    │   ├── test-users.ts            ← shared test account factories
    │   └── api-client.ts            ← thin wrapper for backend setup calls
    ├── pages/                       ← Page Object Models (optional, see below)
    │   └── invoice-list.page.ts
    └── specs/
        ├── billing/
        │   ├── list-invoices.spec.ts
        │   ├── create-invoice.spec.ts
        │   └── cancel-invoice.spec.ts
        └── auth/
            └── login.spec.ts
```

- **`fixtures/`** holds the test-user factory and the thin API client used to set up state without going through the UI.
- **`pages/`** holds Page Object Models if you want them. They're optional — for simple apps it's fine to write selectors inline. Use them when a selector is reused across 3+ specs.
- **`specs/`** mirrors the backend's feature structure. If the backend has `Domain/Billing/Invoicing/`, the frontend specs live under `specs/billing/`.

## The golden rule: set up state via the API, exercise behavior via the UI

Don't click through the UI to create test data. Instead:

```typescript
import { test, expect } from '@playwright/test';
import { apiClient } from '../../fixtures/api-client';
import { testUsers } from '../../fixtures/test-users';

test('user can cancel an unpaid invoice', async ({ page }) => {
  // Setup: create state via the API. No UI clicking.
  const user = await testUsers.createBillingAdmin();
  const invoice = await apiClient.as(user).createInvoice({
    customerId: 'cust-123',
    amountCents: 5000,
    currency: 'USD',
  });

  // Exercise: walk the UI flow we're actually testing.
  await page.goto(`/billing/invoices/${invoice.id}`);
  await page.getByRole('button', { name: 'Cancel invoice' }).click();
  await page.getByRole('button', { name: 'Confirm cancel' }).click();

  // Assert: observable outcome in the UI.
  await expect(page.getByText('Invoice canceled')).toBeVisible();

  // Verify: the backend actually changed state.
  const updated = await apiClient.as(user).getInvoice(invoice.id);
  expect(updated.status).toBe('canceled');
});
```

Why this shape: the UI flow for "cancel an invoice" is one or two clicks. If you also test "create the invoice first" through the UI, every cancel-invoice test becomes flaky because it depends on the create-invoice UI flow not regressing simultaneously. Separate the concerns. The create-invoice spec tests that UI; every other spec sets up invoices via the API.

## Selectors

In order of preference:

1. **`getByRole` with a name.** `getByRole('button', { name: 'Cancel invoice' })`. Accessibility-respecting, stable, and screaming at you if the button isn't accessible.
2. **`getByLabel`** for form fields.
3. **`getByTestId`** using `data-testid` attributes the frontend team commits to. Use this for complex widgets where `getByRole` is ambiguous.
4. **CSS selectors as a last resort.** `.invoice-row:nth-child(3)` is a test ready to break on the next redesign.

Never use selectors that encode implementation details the designer can change without the developer knowing — class names, tag structure, DOM order, color. Tests should break when the *behavior* breaks, not when the *styling* changes.

## Suites

Tag every spec so CI can slice them:

```typescript
test.describe('create invoice @smoke @billing', () => {
  // ...
});
```

- **`@smoke`** — must pass on every PR. Keep the smoke suite under 60 seconds of wall-clock time.
- **`@regression`** — runs on merge to main. Can take several minutes.
- **`@slow`** — intentionally slow end-to-end journeys that exercise real third-party integrations. Run nightly.

## Test users and isolation

Each test MUST create its own users and its own data. No shared fixtures that mutate. The backend test harness provides a test-only API route (or CLI tool) for creating users; use it through the `testUsers` factory in `fixtures/`.

For truly parallel-safe isolation, each test should work inside its own tenant / workspace / scope, so two tests running in parallel don't see each other's invoices. If your backend supports multi-tenancy, use it; if it doesn't, serialize or use per-test random IDs for all visible names.

## What NOT to test with Playwright

- **Unit logic.** If a Date utility needs a test, put it in a unit test file, not a Playwright spec.
- **Every component state.** Playwright tests are expensive. One happy-path spec per user journey is usually enough. Edge cases go in the backend Service tests.
- **Visual appearance.** Playwright can do visual regression, but it's a separate tooling concern and we don't prescribe it here.
- **Performance.** Playwright will show you when a page is slow but it's not a load-testing tool. Use a dedicated tool for that.

## Running Playwright tests alongside the AI Forging loop

Playwright tests are NOT part of the Fire stage of the forge. They run:

- In CI on every PR (the `@smoke` subset).
- On demand locally when you're debugging a specific user journey.
- On merge (the full `@smoke + @regression` suite).

Do not wait for Playwright tests in the Red/Green/Refactor inner loop. The backend's Service and Repository tests are what you iterate against; Playwright is the safety net at the contract boundary.

## Related

- `frontend-testing/README.md`
- `tdd/test-harness-requirements.md` — the backend harness the API setup hits
- `architecture/repositories.md` — why the backend Service tests catch most of what matters

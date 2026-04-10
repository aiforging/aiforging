# Frontend Testing (Optional Layer)

## Why this is optional

The AI Forging framework deliberately pushes business logic to the backend. Frontends should be "dumb" — they render state, handle presentation concerns, and defer anything with a business rule to API calls. Under that model, backend tests cover the behavior that matters, and frontend unit tests can feel like ceremony without value.

That said, **there is one frontend testing layer that earns its keep**: integration tests that exercise the contract between the frontend and the backend through a real browser against a running stack. These catch:

- Breaking changes to API shape that backend tests miss because they only test the backend.
- Form flows and navigation regressions that break the user's journey even though the component unit tests still pass.
- Auth flows, session handling, and CSRF/CORS bugs that only manifest cross-origin.
- Accessibility regressions you can assert on programmatically.

That's what this layer is for. It's still opt-in — the framework does not require it — but if you want frontend tests, this is the only layer we prescribe.

## What's in here

- `playwright-conventions.md` — how to structure Playwright tests in a project that follows the AI Forging architectural conventions on the backend.

## What's NOT in here

- **Component unit tests.** Testing that `<Button onClick={...}>` calls the handler is a Jest/Vitest thing and it's fine if your team wants it, but we don't prescribe it. If your components have so much logic that they need isolated unit tests, the logic probably belongs on the backend.
- **Storybook / visual regression.** Useful, but out of scope for this framework.
- **End-to-end tests that spin up the full production stack including external services.** That's a different animal and needs its own decision process about what you're actually willing to call in CI.

## Default posture when this layer is installed

- Tests live under `tests/e2e/` or `e2e/` at the frontend project root, mirroring the backend's domain-per-folder shape where possible: one folder per user-facing feature, one test file per user journey.
- Tests run against a locally-started backend (Docker Compose, test harness, whatever the project already uses for backend integration tests).
- Tests exercise the real browser via Playwright. Headless in CI, headed locally for debugging.
- Tests do not use mocked API responses. If you're mocking the backend, you're testing the mocks.
- Tests use `data-testid` attributes for stable selectors. Semantic roles (`getByRole('button', { name: '...' })`) are preferred when they're stable.
- Tests are tagged by suite (`@smoke`, `@regression`, `@slow`) so CI can run a fast subset on every PR and the full set on merge.

## When Claude should skip this layer

- User explicitly says no during `/aiforging:setup`.
- Frontend project is a tiny static site or a marketing page.
- Frontend project is pre-production and still in heavy UX iteration; invest in these tests after the interaction design stabilizes.

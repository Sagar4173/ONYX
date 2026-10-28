# Contributing to ONYX

Contributions are welcome. Keep changes focused, tested, and consistent with
the existing architecture.

---

## Development Setup

### Backend

```powershell
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `SECRET_KEY` and `MONGODB_URI` in `backend/.env`.

Linux/macOS equivalent:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

The development server expects the backend on `http://127.0.0.1:8000`.

---

## Workflow

1. Create a branch from `master`.
2. Make the smallest complete change.
3. Add or update tests.
4. Run the relevant verification commands.
5. Update living documentation.
6. Open a pull request against `master`.

```bash
git checkout -b feature/your-feature
git add <specific-files>
git commit -m "feat(scope): concise description"
git push origin feature/your-feature
```

### Branch names

- `feature/xxx`
- `fix/xxx`
- `docs/xxx`
- `refactor/xxx`

### Commit messages

```text
type(scope): description
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

---

## Code Standards

### Backend

- Python 3.13.
- Use type hints where the existing module does.
- Keep route handlers thin; place business logic in `services/`.
- Use Pydantic models for request/response contracts.
- Use Beanie for MongoDB documents.
- Preserve async I/O behavior; do not block the event loop with subprocesses or
  heavy CPU work.
- Validate and sanitize external input, especially repository URLs, webhooks,
  uploaded files, and AI output.
- Never log tokens, passwords, authorization headers, or credential-bearing
  URLs.

### Frontend

- React 18 functional components and hooks.
- Reuse existing UI components and Tailwind conventions.
- Use React Query for server state where the surrounding code does.
- Add API methods to `src/services/api.js`.
- Preserve loading, empty, error, and responsive states.
- Do not embed credentials or environment-specific hosts in components.

### Documentation

- Use the present tense and describe current behavior, not planned behavior.
- Update `docs/API.md` when routes or authentication change.
- Update `docs/PROJECT_STATUS.md` when a capability is completed or removed.
- Update deployment/config docs when environment variables or infrastructure
  change.
- Do not rewrite dated plans or `docs/superpowers/specs/`; add an archive note
  instead if context is needed.

---

## Verification

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests\test_specific.py -q
```

Current suite: 938 tests. Prefer targeted tests first, then the full suite for
changes that cross modules.

### Frontend

```powershell
cd frontend
cmd /c "npm test -- --reporter=dot"
cmd /c "npm run lint"
cmd /c "npm run build"
```

Current suite: 413 tests.

### E2E

Start the backend and frontend, then:

```powershell
cd frontend
cmd /c "npm run e2e"
```

Playwright smoke tests require a browser (`npm run e2e:install`) and a reachable
API. The suite is not a substitute for authenticated integration testing.

### Formatting and whitespace

```powershell
git diff --check
```

Do not run broad formatting or refactoring across unrelated files.

---

## Database and Migration Rules

- Never assume test data can be deleted from a live database.
- Add indexes for new query patterns.
- Avoid destructive migrations without explicit approval.
- Preserve backward compatibility where existing records are involved.
- Use transactions for multi-document operations that must be atomic.
- Verify Beanie model/index changes with a real MongoDB when practical.

---

## AI Changes

- Treat provider output as untrusted.
- Validate structured output before applying it.
- Preserve the configured provider fallback behavior.
- Do not make auto-fix actions autonomous; approval gates are required.
- Add evaluation cases for prompt, retrieval, or triage behavior when practical.
- Keep prompts free of secrets and unnecessary user data.

---

## Pull Request Process

1. Branch from `master`.
2. Implement and test.
3. Run relevant backend/frontend checks.
4. Update living docs.
5. Request review.
6. Address findings with evidence.
7. Merge only after required checks pass.

Include in the PR description:

- what changed
- why it changed
- how it was verified
- known limitations or follow-up work

Do not commit `.env` files, credentials, generated test artifacts, or internal
agent ledgers such as `.superpowers/`.

---

## Need Help?

Use GitHub Issues for bugs and GitHub Discussions for questions. For security
issues, follow [SECURITY.md](../SECURITY.md) and report privately.

# Contributing to ONYX

We welcome contributions! Here's how to get started.

---

## Development Setup

```bash
git clone https://github.com/Sagar4173/ONYX.git
cd ONYX

# Backend
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## Workflow

```bash
git checkout -b feature/your-feature
# Make changes, commit, push
git push origin feature/your-feature
# Create Pull Request on GitHub
```

### Branch naming
- `feature/xxx` - new features
- `fix/xxx` - bug fixes
- `docs/xxx` - documentation
- `refactor/xxx` - code restructure

### Commit convention
```
type(scope): description

feat: new feature
fix: bug fix
docs: documentation
refactor: code restructure
test: tests
chore: maintenance
```

---

## Code Standards

### Python Backend
- Python 3.13+
- Type hints required for all functions
- Async/await for I/O operations
- Pydantic models for all API schemas
- Beanie ODM for MongoDB documents

### React Frontend
- React 18 functional components with hooks
- Tailwind CSS for styling
- React Query for server state
- Services in `api.js` for API calls

---

## Testing

```bash
# Backend (347 tests)
cd backend
python -m pytest tests/ -q

# Frontend (172 tests)
cd frontend
npm test

# E2E (requires running backend + frontend)
npm run e2e
```

---

## Pull Request Process

1. Create branch from `main`
2. Implement and test
3. Push and create PR
4. Request review
5. Address feedback
6. Merge after approval

---

## Documentation

- Update `API.md` for new/ changed endpoints
- Update `PROJECT_STATUS.md` for completed features
- Update relevant doc in `docs/`

---

## Need Help?

- GitHub Issues for bug reports
- GitHub Discussions for questions

# Contributing to UDT-X Platform

Thank you for your interest in contributing to the **Unified Dynamic Threat Identification and Defense Platform (UDT-X)**! We welcome contributions from the cybersecurity, machine learning, and systems engineering communities.

---

## 🛠️ Development Setup & Workflow

### 1. Prerequisites
- **Python 3.12+** / **Python 3.14**
- **Node.js 20+** & **npm**
- **Docker Desktop** (with Docker Compose v2)
- **Git**

### 2. Environment Initialization
```bash
# Clone the repository
git clone https://github.com/your-org/udtx.git
cd udtx

# Create virtual environment and install backend dependencies
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
pip install -r services/api/requirements.txt
pip install -r services/api/requirements-dev.txt

# Install frontend dependencies
cd dashboard
npm install
cd ..
```

---

## 🧪 Testing & Code Quality Guidelines

Before submitting any Pull Request, ensure that all automated checks and tests pass with zero errors:

### Backend Testing (Pytest)
```bash
pytest -v
```
*Requirement: All 111+ test suites covering schema validation, heuristics, ML inference, and API endpoints must pass.*

### Python Code Formatting & Linting (Ruff)
```bash
ruff check .
ruff format . --check
```

### Frontend Typecheck & Build
```bash
cd dashboard
npm run build
cd ..
```

---

## 🔀 Pull Request Process

1. **Fork the Repository:** Create a feature branch off `main` (`feature/your-feature-name` or `bugfix/issue-description`).
2. **Atomic Commits:** Make clear, descriptive commit messages following the Conventional Commits specification (e.g., `feat(engine): add entropy threshold check`, `fix(api): correct cors preflight routing`).
3. **Write Unit Tests:** Add comprehensive pytest cases under `tests/` for any new detection heuristics, normalizers, or API endpoints.
4. **Update Documentation:** If modifying models, schemas, or architectures, update relevant markdown documents under `docs/`.
5. **Open Pull Request:** Provide a clear description of changes, linked issues, and benchmark results.

---

## 🛡️ Safety Notice for Simulation Traffic

When working on `replay_lab/`:
- Never configure tests or scenarios to emit traffic on non-loopback or production physical interfaces.
- The `replay_lab/safety.py` safety validator must remain active and unmodified.

---

## 💬 Community & Support

- Open an issue on GitHub for bug reports and feature requests.
- For security disclosures, please follow [SECURITY.md](SECURITY.md).

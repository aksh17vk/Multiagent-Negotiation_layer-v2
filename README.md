# Multiagent Negotiation Layer (MNL)

**Agents negotiate. Evidence decides.**

## Clone Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Multiagent-Negotiation_layer-v2
```

## Backend Setup

```bash
cd apps/agent-runtime
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install dependencies using the available manifest:

```powershell
if (Test-Path requirements.txt) {
    python -m pip install -r requirements.txt
} elseif (Test-Path pyproject.toml) {
    python -m pip install .
}
```

## Run Backend

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## API Documentation

http://127.0.0.1:8000/docs

## Run Tests

```bash
python -m pytest -q
```

## Git Workflow

```bash
git pull --rebase origin main
git status
git add <specific-files>
git diff --cached
git commit -m "describe your changes"
git push origin main
```

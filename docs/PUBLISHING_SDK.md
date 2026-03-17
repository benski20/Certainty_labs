# Publishing the Certainty Labs SDK to PyPI

See `sdk/` for the package. This doc covers official PyPI publication.

## Is the SDK ready?

Yes. The SDK is ready for official publication:

- **pyproject.toml** — Hatchling build, metadata, classifiers
- **README.md** — Install, quick start, API reference
- **Dependencies** — `httpx>=0.27.0` only
- **API** — Fixed base URL, `CERTAINTY_API_KEY` from env
- **Tests** — Integration tests pass against live API

## Prerequisites

1. **PyPI account** — [pypi.org/account/register](https://pypi.org/account/register)
2. **Package name** — Check availability: `certaintylabs` may already exist; consider `certainty-labs` if needed
3. **Repository** — Ensure `[project.urls].Repository` in pyproject.toml points to a real repo (e.g. GitHub)

## Publish steps

### 1. Bump version (if needed)

Edit `sdk/pyproject.toml`:

```toml
version = "0.1.0"  # → "0.1.1" for patch, "0.2.0" for minor
```

### 2. Build

```bash
cd sdk
hatch build
```

Creates `dist/certaintylabs-0.1.0-py3-none-any.whl` and `dist/certaintylabs-0.1.0.tar.gz`.

### 3. Publish to PyPI

**Option A: Hatch (recommended)**

```bash
cd sdk
hatch publish
```

Prompts for PyPI username and password (or token). Use an API token: username `__token__`, password `pypi-...`.

**Option B: Twine**

```bash
cd sdk
pip install twine
hatch build
twine upload dist/*
```

### 4. Test install

```bash
pip install certaintylabs
python -c "from certaintylabs import Certainty; print(Certainty().health())"
```

## Trusted Publishers (optional)

For CI/CD or token-free publishing, set up [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/):

1. PyPI project → Publishing → Add a new publisher
2. Choose GitHub Actions (or other)
3. Add the workflow and environment

## TestPyPI (for dry runs)

```bash
hatch publish -p pypi --repo https://test.pypi.org/legacy/
```

Install from TestPyPI: `pip install --index-url https://test.pypi.org/simple/ certaintylabs`

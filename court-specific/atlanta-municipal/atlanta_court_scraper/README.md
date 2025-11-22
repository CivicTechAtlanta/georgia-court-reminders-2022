# Atlanta Court Scraper

Python client for searching court cases in the Atlanta Municipal Court system (Tyler Technologies Benchmark platform).

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to project
cd $(git rev-parse --show-toplevel)/scraper/atlanta-court-scraper

# Install dependencies
uv sync
```

## Configuration (Optional)

```bash
cp .env.example .env
# Edit .env to customize COURT_BASE_URL and LOG_LEVEL
```

## Usage

### CLI Examples

```bash
# Search by name
uv run atlanta-court search --name "Doe, John"

# Search by case number
uv run atlanta-court search --case-number "25TR059183"

# With date range and output file
uv run atlanta-court search --name "Smith, Jane" \
  --opened-from 2024-01-01 \
  --opened-to 2024-12-31 \
  --output results.json
```

### Python API

```python
from atlanta_court import AtlantaMunicipalClient

# Simple usage
with AtlantaMunicipalClient() as client:
    results = client.search_and_get_results("Smith, Jane", max_results=50)
    print(f"Found {len(results)} cases")
```

## Key Methods

- `search()` - Perform a search and initialize session
- `get_results_data(start, length)` - Retrieve paginated results
- `search_and_get_results(search_term, max_results)` - Convenience method

Search types: `SEARCH_TYPE_NAME`, `SEARCH_TYPE_CASE_NUMBER`, `SEARCH_TYPE_ATTORNEY`

## Development

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=atlanta_court --cov-report=term-missing
```

## How It Works

Handles Tyler Technologies Benchmark platform authentication:
1. Loads search page to obtain session cookie and anti-CSRF tokens
2. Posts search with CSRF token
3. Fetches paginated results via AJAX

## License

MIT

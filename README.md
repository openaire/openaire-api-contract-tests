# OpenAIRE Search API Contract Tests

A two-phase test suite to verify that the OpenAIRE Publications Search API
(`https://api.openaire.eu/search/publications`) maintains its contract after a
backend storage-layer switch.

## How it works

| Phase | Command | What happens |
|-------|---------|--------------|
| **Record** (before switch) | `pytest --phase=record` | Queries the API for every test case and saves responses as JSON snapshots under `snapshots/`. |
| **Compare** (after switch) | `pytest --phase=compare` | Re-runs the exact same queries and asserts that the new responses match the stored snapshots. |

A *match* means the response contains the same set of result identifiers in the
same order and the key metadata fields are identical, which is the definition of
"contract fulfilled".

## Quick start

```bash
# 0. Initialize virtual environment
cd openaire-api-contract-tests
source .venv/bin/activate

# 1. Install dependencies (Python ≥ 3.9)
pip install -r requirements.txt

# 2. Record baseline snapshots (run BEFORE the switch)
pytest --phase=record -v

# 3. After the storage switch, compare against the baseline
pytest --phase=compare -v
```

## Configuration

| Environment variable | Default | Description |
|----------------------|---------|-------------|
| `OPENAIRE_API_BASE_URL` | `https://api.openaire.eu` | Override the base URL (useful for staging environments). |
| `OPENAIRE_ENDPOINT` | `search/publications` | Override the endpoint path (useful for testing alternative endpoints). |
| `OPENAIRE_SNAPSHOT_DIR` | `snapshots` | Directory where baseline snapshots are stored. |
| `OPENAIRE_REQUEST_TIMEOUT` | `60` | HTTP request timeout in seconds. |
| `OPENAIRE_RETRY_COUNT` | `3` | Number of retries on transient HTTP errors. |
| `OPENAIRE_RETRY_DELAY` | `5` | Seconds between retries. |

All of the above can also be set via CLI flags (`--base-url`, `--endpoint`,
`--snapshot-dir`).

### Testing two different endpoints for compliance

Record a baseline from the original endpoint, then compare against the new one:

```bash
# Record from the current endpoint
pytest --phase=record --endpoint=search/publications -v

# Compare against a different endpoint (or a different base URL)
pytest --phase=compare --endpoint=search/publications-v2 -v

# …or compare across different hosts
pytest --phase=record  --base-url=https://api.openaire.eu -v
pytest --phase=compare --base-url=https://beta-api.openaire.eu -v
```

## Test cases covered

The suite exercises the following API capabilities on the
`/search/publications` endpoint:

- **Keyword search** (`keywords`)
- **DOI lookup** (`doi`)
- **ORCID-based search** (`orcid`)
- **Title search** (`title`)
- **Author search** (`author`)
- **Date range filtering** (`fromDateAccepted` / `toDateAccepted`)
- **Open Access filtering** (`OA`)
- **Funder filtering** (`funder`, `hasECFunding`)
- **Country filtering** (`country`)
- **Sorting** (`sortBy`)
- **Pagination** (`page`, `size`)
- **Peer-reviewed** (`peerReviewed`)
- **Diamond journal** (`diamondJournal`)
- **Publicly funded** (`publiclyFunded`)
- **Green OA** (`green`)
- **OA colour** (`openAccessColor`)
- **SDG classification** (`sdg`)
- **Field of Science** (`fos`)
- **Influence / popularity / citation count / impulse**
- **OpenAIRE publication ID** (`openairePublicationID`)
- **Project link** (`hasProject`, `projectID`)
- **Provider filtering** (`openaireProviderID`)
- **Response format** (`format=json`, `format=xml`)
- **Combined filters** (multiple parameters together)

## Snapshot format

Each snapshot is a JSON file named after the test case, stored in the
`snapshots/` directory.  The file contains the query parameters used and the
normalised response (result identifiers + key metadata).

## Comparison logic

During the *compare* phase the suite checks:

1. **Same total result count** (within a configurable tolerance for very large
   result sets).
2. **Same result identifiers** in the same order for the page retrieved.
3. **Same key metadata fields** for each result (title, authors, date of
   acceptance, DOI, access rights).

Fields that are expected to change (e.g., timestamps of last indexing) are
excluded from comparison.

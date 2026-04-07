# OpenAIRE Search API Contract Tests

A two-phase test suite to verify that the OpenAIRE Search API endpoints
maintain their contract after a backend storage-layer switch.

## Endpoints covered

| Endpoint | Test file | Snapshot directory |
|----------|-----------|-------------------|
| `/search/publications` | `test_publications_contract.py` | `snapshots_publications/` |
| `/search/datasets` | `test_datasets_contract.py` | `snapshots_datasets/` |
| `/search/software` | `test_software_contract.py` | `snapshots_software/` |
| `/search/other` | `test_other_contract.py` | `snapshots_other/` |
| `/search/projects` | `test_projects_contract.py` | `snapshots_projects/` |

## How it works

| Phase | Command | What happens |
|-------|---------|--------------|
| **Record** (before switch) | `pytest --phase=record` | Queries every endpoint for every test case and saves responses as JSON snapshots in per-endpoint directories. |
| **Compare** (after switch) | `pytest --phase=compare` | Re-runs the exact same queries and asserts that the new responses match the stored snapshots. |

A *match* means the response is **structurally equivalent** to the baseline.
For multi-result queries this is verified with **loose comparison** by default:
the total result count may differ by up to 10 %, and the result-set overlap
(by object identifier) must be at least 50 %.  Single-result lookups (e.g. by
DOI or grant ID) use strict field-by-field comparison.

## Quick start

```bash
# 0. Initialize virtual environment
cd openaire-api-contract-tests
python3 -m venv .venv
source .venv/bin/activate

# 1. Install dependencies (Python ≥ 3.9)
pip install -r requirements.txt

# 2. Record baseline snapshots (run BEFORE the switch)
pytest --phase=record -v

# 3. After the storage switch, compare against the baseline
pytest --phase=compare -v

# Run a specific endpoint only
pytest test_datasets_contract.py --phase=record -v
pytest test_projects_contract.py --phase=compare -v
```

## Configuration

| Environment variable | Default | Description |
|----------------------|---------|-------------|
| `OPENAIRE_API_BASE_URL` | `https://api.openaire.eu` | Override the base URL (useful for staging environments). |
| `OPENAIRE_ENDPOINT` | `search/publications` | Override the endpoint path (publications test only). |
| `OPENAIRE_SNAPSHOT_DIR` | auto per-endpoint | Override the root snapshot directory. |
| `OPENAIRE_REQUEST_TIMEOUT` | `60` | HTTP request timeout in seconds. |
| `OPENAIRE_RETRY_COUNT` | `3` | Number of retries on transient HTTP errors. |
| `OPENAIRE_RETRY_DELAY` | `5` | Seconds between retries. |

All of the above can also be set via CLI flags (`--base-url`, `--endpoint`,
`--snapshot-dir`).

### Testing two different API instances for compliance

```bash
# Record from the current instance
pytest --phase=record --base-url=https://api.openaire.eu -v

# Compare against a different instance
pytest --phase=compare --base-url=https://beta-api.openaire.eu -v
```

## Test cases covered

### Research products (publications, datasets, software, other)

All four research-product endpoints share the same general parameters.
Each test file exercises:

- **Keyword search** (`keywords`)
- **DOI lookup** (`doi`)
- **ORCID-based search** (`orcid`)
- **Title search** (`title`)
- **Author search** (`author`)
- **Date range filtering** (`fromDateAccepted` / `toDateAccepted`)
- **Open Access filtering** (`OA`)
- **Funder filtering** (`funder`, `hasECFunding`, `hasWTFunding`)
- **Country filtering** (`country`)
- **Sorting** (`sortBy`)
- **Pagination** (`page`, `size`)
- **Influence / popularity / citation count / impulse**
- **Project link** (`hasProject`)
- **Provider filtering** (`openaireProviderID`)
- **Response format** (`format=json`, `format=xml`)
- **Combined filters** (multiple parameters together)

The **publications** test file additionally covers:
- **Peer-reviewed** (`peerReviewed`)
- **Diamond journal** (`diamondJournal`)
- **Publicly funded** (`publiclyFunded`)
- **Green OA** (`green`)
- **OA colour** (`openAccessColor`)
- **SDG classification** (`sdg`)
- **Field of Science** (`fos`)
- **OpenAIRE publication ID** (`openairePublicationID`)

### Projects

The projects endpoint has a distinct parameter set and metadata schema:

- **Keyword search** (`keywords`)
- **Grant ID lookup** (`grantID`)
- **Project name search** (`name`)
- **Acronym search** (`acronym`)
- **Call ID** (`callID`)
- **Funder filtering** (`funder`, `hasECFunding`, `hasWTFunding`)
- **Start/end year** (`startYear`, `endYear`)
- **Participant countries** (`participantCountries`)
- **Participant institutions** (`participantAcronyms`)
- **FP7 scientific area** (`FP7scientificArea`)
- **Funding stream** (`fundingStream`)
- **Sorting** (`sortBy` with project-specific fields)
- **Pagination** (`page`, `size`)
- **Response format** (`format=json`, `format=xml`)
- **Combined filters**

## Snapshot format

Each snapshot is a JSON file named after the test case, stored in the
appropriate per-endpoint directory (e.g. `snapshots_publications/`,
`snapshots_projects/`).  The file contains the query parameters used and the
normalised response (result identifiers + key metadata).

## Comparison logic

During the *compare* phase the suite checks:

1. **Total result count** within a configurable tolerance (default 10 % for
   multi-result queries, exact for single-result lookups).
2. **Result-set overlap** — at least 50 % of baseline object identifiers must
   appear in the current results (loose mode, the default for multi-result
   queries).
3. **Strict field-by-field match** for single-result lookups (by DOI, grant ID,
   OpenAIRE ID, etc.).

Fields that are expected to change (e.g., timestamps of last indexing) are
excluded from comparison.

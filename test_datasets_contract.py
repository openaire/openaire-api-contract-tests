"""
OpenAIRE Search Datasets API – Contract Test Suite
====================================================

Exercises the ``/search/datasets`` endpoint with the general research-product
parameters plus the dataset-specific ``openaireDatasetID`` parameter.

Modes
-----
* ``--phase=record``  – call the API and persist the normalised response as a
  baseline snapshot.
* ``--phase=compare`` – call the API, normalise, and assert equivalence with
  the stored baseline.

Run with::

    pytest test_datasets_contract.py --phase=record -v
    pytest test_datasets_contract.py --phase=compare -v
"""

import os

import pytest

from helpers import (
    DEFAULT_TOTAL_TOLERANCE_PCT,
    query_api,
    normalise_json_response,
    normalise_xml_response,
    save_snapshot,
    load_snapshot,
    compare_snapshots,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_test(
    test_id: str,
    params: dict,
    base_url: str,
    endpoint: str,
    snapshot_dir: str,
    phase: str,
    *,
    fmt: str = "json",
    total_tolerance_pct: float = DEFAULT_TOTAL_TOLERANCE_PCT,
    loose: bool = True,
):
    """
    Core test driver.

    By default tests use *loose* comparison and a generous total-count
    tolerance because different backend instances may have slightly
    different index contents.
    """
    status, body, request_url = query_api(base_url, endpoint, params, fmt=fmt)
    assert status == 200, f"Expected HTTP 200, got {status}\n  URL: {request_url}"

    if fmt == "json":
        current = normalise_json_response(body)
    else:
        current = normalise_xml_response(body)

    if phase == "record":
        save_snapshot(snapshot_dir, test_id, params=params, normalised=current)
    else:
        compare_dir = snapshot_dir.rstrip('/') + '_compare'
        os.makedirs(compare_dir, exist_ok=True)
        save_snapshot(compare_dir, test_id, params=params, normalised=current)

        baseline_data = load_snapshot(snapshot_dir, test_id)
        baseline = baseline_data["normalised"]
        diffs = compare_snapshots(
            baseline, current,
            total_tolerance_pct=total_tolerance_pct,
            loose=loose,
        )
        assert not diffs, (
            f"Contract differences detected:\n"
            f"  URL: {request_url}\n"
            + "\n".join(f"  • {d}" for d in diffs)
        )


# ===================================================================
# 1. Keyword search
# ===================================================================

class TestKeywordSearch:
    """Search datasets by keywords."""

    def test_single_keyword(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "keyword_single",
            {"keywords": "climate", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_multiple_keywords(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "keyword_multiple",
            {"keywords": "genome sequencing", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 2. DOI lookup
# ===================================================================

class TestDOILookup:
    """Retrieve datasets by DOI."""

    def test_single_doi(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "doi_single",
            {"doi": "10.5281/zenodo.3234", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
            loose=False,
        )


# ===================================================================
# 3. Title search
# ===================================================================

class TestTitleSearch:
    """Search datasets by title."""

    def test_title(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "title_search",
            {"title": "ocean temperature", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 4. Author search
# ===================================================================

class TestAuthorSearch:
    """Search datasets by author."""

    def test_author(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "author_search",
            {"author": "Smith", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 5. ORCID search
# ===================================================================

class TestORCIDSearch:
    """Search datasets by ORCID."""

    def test_orcid(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "orcid",
            {"orcid": "0000-0002-9079-593X", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 6. Date range filtering
# ===================================================================

class TestDateRange:
    """Filter datasets by date range."""

    def test_from_date(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "date_from",
            {
                "keywords": "biodiversity",
                "fromDateAccepted": "2023-01-01",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_date_range(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "date_range",
            {
                "keywords": "air quality",
                "fromDateAccepted": "2022-01-01",
                "toDateAccepted": "2022-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 7. Open Access filtering
# ===================================================================

class TestOpenAccess:
    """Filter datasets by Open Access status."""

    def test_open_access_true(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "oa_true",
            {"keywords": "satellite imagery", "OA": "true", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_open_access_false(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "oa_false",
            {"keywords": "satellite imagery", "OA": "false", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 8. Funder filtering
# ===================================================================

class TestFunderFiltering:
    """Filter datasets by funder."""

    def test_funder_ec(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "funder_ec",
            {"funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_funder_nsf(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "funder_nsf",
            {"funder": "NSF", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_has_ec_funding_true(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "has_ec_funding_true",
            {"hasECFunding": "true", "keywords": "energy", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 9. Country filtering
# ===================================================================

class TestCountryFiltering:
    """Filter datasets by country."""

    def test_country_de(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "country_de",
            {"country": "DE", "keywords": "ecology", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_country_gb(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "country_gb",
            {"country": "GB", "keywords": "meteorology", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 10. Sorting
# ===================================================================

class TestSorting:
    """Verify sorted result ordering is preserved."""

    def test_sort_by_date_descending(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "sort_date_desc",
            {
                "keywords": "proteomics",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_sort_by_date_ascending(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "sort_date_asc",
            {
                "keywords": "proteomics",
                "sortBy": "resultdateofacceptance,ascending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 11. Pagination
# ===================================================================

class TestPagination:
    """Ensure pagination returns consistent slices."""

    def test_page_1(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "pagination_p1",
            {"keywords": "geophysics", "size": "5", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_page_2(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "pagination_p2",
            {"keywords": "geophysics", "size": "5", "page": "2"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_large_page_size(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "pagination_large",
            {"keywords": "geophysics", "size": "50", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 12. Impact indicators
# ===================================================================

class TestImpactIndicators:
    """Filter datasets by bibliometric impact indicators."""

    def test_influence_c1(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "influence_c1",
            {"influence": "C1", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_popularity_c2(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "popularity_c2",
            {"popularity": "C2", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_citation_count_c3(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "citation_count_c3",
            {"citationCount": "C3", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_impulse_c1(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "impulse_c1",
            {"impulse": "C1", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 13. Project-linked datasets
# ===================================================================

class TestProjectLinked:
    """Search for datasets linked to projects."""

    def test_has_project_true(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "has_project_true",
            {"hasProject": "true", "keywords": "sensor data", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 14. Provider filtering
# ===================================================================

class TestProviderFiltering:
    """Filter by data provider."""

    def test_provider_zenodo(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "provider_zenodo",
            {
                "openaireProviderID": "opendoar____::358aee4cc897452c00244351e4d91f69",
                "keywords": "dataset",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )


# ===================================================================
# 15. XML format
# ===================================================================

class TestXMLFormat:
    """Verify that XML responses maintain the same contract."""

    def test_xml_keyword_search(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "xml_keyword",
            {"keywords": "hydrology", "size": "10", "page": "1"},
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
            fmt="xml",
        )


# ===================================================================
# 16. Combined filters
# ===================================================================

class TestCombinedFilters:
    """Test queries that combine multiple filter parameters."""

    def test_keyword_oa_country_date(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "combined_kw_oa_country_date",
            {
                "keywords": "soil moisture",
                "OA": "true",
                "country": "DE",
                "fromDateAccepted": "2021-01-01",
                "toDateAccepted": "2023-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

    def test_funder_sorted(self, base_url, endpoint_datasets, snapshot_dir_datasets, phase):
        _run_test(
            "combined_funder_sorted",
            {
                "funder": "EC",
                "keywords": "environment",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_datasets, snapshot_dir_datasets, phase,
        )

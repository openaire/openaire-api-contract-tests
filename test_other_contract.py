"""
OpenAIRE Search Other Research Products API – Contract Test Suite
==================================================================

Exercises the ``/search/other`` endpoint with the general research-product
parameters plus the other-specific ``openaireOtherID`` parameter.

Modes
-----
* ``--phase=record``  – call the API and persist the normalised response as a
  baseline snapshot.
* ``--phase=compare`` – call the API, normalise, and assert equivalence with
  the stored baseline.

Run with::

    pytest test_other_contract.py --phase=record -v
    pytest test_other_contract.py --phase=compare -v
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
    fmt: str = "xml",
    total_tolerance_pct: float = DEFAULT_TOTAL_TOLERANCE_PCT,
    loose: bool = True,
):
    """Core test driver – loose comparison by default."""
    status, body, request_url, response_time_ms = query_api(base_url, endpoint, params, fmt=fmt)
    assert status == 200, f"Expected HTTP 200, got {status}\n  URL: {request_url}"

    if fmt == "json":
        current = normalise_json_response(body)
    else:
        current = normalise_xml_response(body)

    print(f"  [timing] {test_id}: {response_time_ms:.0f} ms")

    if phase == "record":
        save_snapshot(snapshot_dir, test_id, params=params, normalised=current, response_time_ms=response_time_ms)
    else:
        compare_dir = snapshot_dir.rstrip('/') + '_compare'
        os.makedirs(compare_dir, exist_ok=True)
        save_snapshot(compare_dir, test_id, params=params, normalised=current, response_time_ms=response_time_ms)

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
            + "\n".join(f"  \u2022 {d}" for d in diffs)
        )

class TestKeywordSearch:
    """Search other research products by keywords."""

    def test_single_keyword(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "single_keyword",
            {"keywords": "report", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_multiple_keywords(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "multiple_keywords",
            {"keywords": "policy brief education", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 2. DOI lookup
# ===================================================================

class TestDOILookup:
    """Retrieve other research products by DOI."""

    def test_single_doi(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "single_doi",
            {"doi": "10.5281/zenodo.5678", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
            loose=False,
        )


# ===================================================================
# 3. Title search
# ===================================================================

class TestTitleSearch:
    """Search other research products by title."""

    def test_title(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "title",
            {"title": "technical report analysis", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 4. Author search
# ===================================================================

class TestAuthorSearch:
    """Search other research products by author."""

    def test_author(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "author",
            {"author": "Mueller", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 5. ORCID search
# ===================================================================

class TestORCIDSearch:
    """Search other research products by ORCID."""

    def test_orcid(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "orcid",
            {"orcid": "0000-0002-9079-593X", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 6. Date range filtering
# ===================================================================

class TestDateRange:
    """Filter other research products by date range."""

    def test_from_date(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "from_date",
            {
                "keywords": "standards",
                "fromDateAccepted": "2023-01-01",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_date_range(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "date_range",
            {
                "keywords": "deliverable",
                "fromDateAccepted": "2022-01-01",
                "toDateAccepted": "2022-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 7. Open Access filtering
# ===================================================================

class TestOpenAccess:
    """Filter other research products by Open Access status."""

    def test_open_access_true(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "open_access_true",
            {"keywords": "evaluation", "OA": "true", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_open_access_false(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "open_access_false",
            {"keywords": "evaluation", "OA": "false", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 8. Funder filtering
# ===================================================================

class TestFunderFiltering:
    """Filter other research products by funder."""

    def test_funder_ec(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "funder_ec",
            {"funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_funder_nsf(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "funder_nsf",
            {"funder": "NSF", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_has_ec_funding_true(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "has_ec_funding_true",
            {"hasECFunding": "true", "keywords": "project output", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 9. Country filtering
# ===================================================================

class TestCountryFiltering:
    """Filter other research products by country."""

    def test_country_de(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "country_de",
            {"country": "DE", "keywords": "documentation", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_country_gb(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "country_gb",
            {"country": "GB", "keywords": "survey", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 10. Sorting
# ===================================================================

class TestSorting:
    """Verify sorted result ordering is preserved."""

    def test_sort_by_date_descending(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "sort_by_date_descending",
            {
                "keywords": "presentation",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_sort_by_date_ascending(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "sort_by_date_ascending",
            {
                "keywords": "presentation",
                "sortBy": "resultdateofacceptance,ascending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 11. Pagination
# ===================================================================

class TestPagination:
    """Ensure pagination returns consistent slices."""

    def test_page_1(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "page_1",
            {"keywords": "lecture", "size": "5", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_page_2(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "page_2",
            {"keywords": "lecture", "size": "5", "page": "2"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_large_page_size(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "large_page_size",
            {"keywords": "lecture", "size": "50", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 12. Impact indicators
# ===================================================================

class TestImpactIndicators:
    """Filter other research products by bibliometric indicators."""

    def test_influence_c1(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "influence_c1",
            {"influence": "C1", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_popularity_c2(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "popularity_c2",
            {"popularity": "C2", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_citation_count_c3(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "citation_count_c3",
            {"citationCount": "C3", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_impulse_c1(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "impulse_c1",
            {"impulse": "C1", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 13. Project-linked other products
# ===================================================================

class TestProjectLinked:
    """Search for other research products linked to projects."""

    def test_has_project_true(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "has_project_true",
            {"hasProject": "true", "keywords": "deliverable", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 14. Provider filtering
# ===================================================================

class TestProviderFiltering:
    """Filter by data provider."""

    def test_provider_zenodo(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "provider_zenodo",
            {
                "openaireProviderID": "opendoar____::358aee4cc897452c00244351e4d91f69",
                "keywords": "poster",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )


# ===================================================================
# 15. XML format
# ===================================================================

class TestJSONFormat:
    """Verify that JSON responses maintain the same contract."""

    def test_json_keyword_search(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "json_keyword_search",
            {"keywords": "workshop", "size": "10", "page": "1"},
            base_url, endpoint_other, snapshot_dir_other, phase,
            fmt="json",
        )


# ===================================================================
# 16. Combined filters
# ===================================================================

class TestCombinedFilters:
    """Test queries that combine multiple filter parameters."""

    def test_keyword_oa_country_date(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "keyword_oa_country_date",
            {
                "keywords": "guidelines",
                "OA": "true",
                "country": "IT",
                "fromDateAccepted": "2021-01-01",
                "toDateAccepted": "2023-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

    def test_funder_sorted(self, base_url, endpoint_other, snapshot_dir_other, phase):
        _run_test(
            "funder_sorted",
            {
                "funder": "EC",
                "keywords": "milestone",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_other, snapshot_dir_other, phase,
        )

"""
OpenAIRE Search Software API – Contract Test Suite
====================================================

Exercises the ``/search/software`` endpoint with the general research-product
parameters plus the software-specific ``openaireSoftwareID`` parameter.

Modes
-----
* ``--phase=record``  – call the API and persist the normalised response as a
  baseline snapshot.
* ``--phase=compare`` – call the API, normalise, and assert equivalence with
  the stored baseline.

Run with::

    pytest test_software_contract.py --phase=record -v
    pytest test_software_contract.py --phase=compare -v
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
    """Core test driver – loose comparison by default."""
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
    """Search software by keywords."""

    def test_single_keyword(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "keyword_single",
            {"keywords": "python", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_multiple_keywords(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "keyword_multiple",
            {"keywords": "machine learning library", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 2. DOI lookup
# ===================================================================

class TestDOILookup:
    """Retrieve software by DOI."""

    def test_single_doi(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "doi_single",
            {"doi": "10.5281/zenodo.1234", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
            loose=False,
        )


# ===================================================================
# 3. Title search
# ===================================================================

class TestTitleSearch:
    """Search software by title."""

    def test_title(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "title_search",
            {"title": "data processing pipeline", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 4. Author search
# ===================================================================

class TestAuthorSearch:
    """Search software by author."""

    def test_author(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "author_search",
            {"author": "Garcia", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 5. ORCID search
# ===================================================================

class TestORCIDSearch:
    """Search software by ORCID."""

    def test_orcid(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "orcid",
            {"orcid": "0000-0002-9079-593X", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 6. Date range filtering
# ===================================================================

class TestDateRange:
    """Filter software by date range."""

    def test_from_date(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "date_from",
            {
                "keywords": "simulation",
                "fromDateAccepted": "2023-01-01",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_date_range(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "date_range",
            {
                "keywords": "visualization",
                "fromDateAccepted": "2022-01-01",
                "toDateAccepted": "2022-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 7. Open Access filtering
# ===================================================================

class TestOpenAccess:
    """Filter software by Open Access status."""

    def test_open_access_true(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "oa_true",
            {"keywords": "analysis tool", "OA": "true", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_open_access_false(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "oa_false",
            {"keywords": "analysis tool", "OA": "false", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 8. Funder filtering
# ===================================================================

class TestFunderFiltering:
    """Filter software by funder."""

    def test_funder_ec(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "funder_ec",
            {"funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_has_ec_funding_true(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "has_ec_funding_true",
            {"hasECFunding": "true", "keywords": "scientific computing", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 9. Country filtering
# ===================================================================

class TestCountryFiltering:
    """Filter software by country."""

    def test_country_de(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "country_de",
            {"country": "DE", "keywords": "software", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_country_gb(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "country_gb",
            {"country": "GB", "keywords": "algorithm", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 10. Sorting
# ===================================================================

class TestSorting:
    """Verify sorted result ordering is preserved."""

    def test_sort_by_date_descending(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "sort_date_desc",
            {
                "keywords": "bioinformatics",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_sort_by_date_ascending(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "sort_date_asc",
            {
                "keywords": "bioinformatics",
                "sortBy": "resultdateofacceptance,ascending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 11. Pagination
# ===================================================================

class TestPagination:
    """Ensure pagination returns consistent slices."""

    def test_page_1(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "pagination_p1",
            {"keywords": "framework", "size": "5", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_page_2(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "pagination_p2",
            {"keywords": "framework", "size": "5", "page": "2"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_large_page_size(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "pagination_large",
            {"keywords": "framework", "size": "50", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 12. Impact indicators
# ===================================================================

class TestImpactIndicators:
    """Filter software by bibliometric impact indicators."""

    def test_influence_c1(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "influence_c1",
            {"influence": "C1", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_popularity_c2(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "popularity_c2",
            {"popularity": "C2", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_citation_count_c3(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "citation_count_c3",
            {"citationCount": "C3", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_impulse_c1(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "impulse_c1",
            {"impulse": "C1", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 13. Project-linked software
# ===================================================================

class TestProjectLinked:
    """Search for software linked to projects."""

    def test_has_project_true(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "has_project_true",
            {"hasProject": "true", "keywords": "toolkit", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 14. Provider filtering
# ===================================================================

class TestProviderFiltering:
    """Filter by data provider."""

    def test_provider_zenodo(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "provider_zenodo",
            {
                "openaireProviderID": "opendoar____::358aee4cc897452c00244351e4d91f69",
                "keywords": "code",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )


# ===================================================================
# 15. XML format
# ===================================================================

class TestXMLFormat:
    """Verify that XML responses maintain the same contract."""

    def test_xml_keyword_search(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "xml_keyword",
            {"keywords": "workflow", "size": "10", "page": "1"},
            base_url, endpoint_software, snapshot_dir_software, phase,
            fmt="xml",
        )


# ===================================================================
# 16. Combined filters
# ===================================================================

class TestCombinedFilters:
    """Test queries that combine multiple filter parameters."""

    def test_keyword_oa_country_date(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "combined_kw_oa_country_date",
            {
                "keywords": "image processing",
                "OA": "true",
                "country": "FR",
                "fromDateAccepted": "2021-01-01",
                "toDateAccepted": "2023-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

    def test_funder_sorted(self, base_url, endpoint_software, snapshot_dir_software, phase):
        _run_test(
            "combined_funder_sorted",
            {
                "funder": "EC",
                "keywords": "data analysis",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_software, snapshot_dir_software, phase,
        )

"""
OpenAIRE Search Publications API – Contract Test Suite
=======================================================

Each test function exercises a specific API use case described in the OpenAIRE
Search API documentation.

Modes
-----
* ``--phase=record``  – call the API and persist the normalised response as a
  baseline snapshot.
* ``--phase=compare`` – call the API, normalise, and assert equivalence with
  the stored baseline.

Run with::

    pytest test_publications_contract.py --phase=record -v
    pytest test_publications_contract.py --phase=compare -v
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
    """
    Core test driver used by every test case.

    * In *record* mode it queries the API, normalises the response, and saves a
      snapshot.
    * In *compare* mode it queries again, normalises, loads the baseline, and
      asserts equality.

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
    """Search by keywords – the most basic query type."""

    def test_single_keyword(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "single_keyword",
            {"keywords": "covid", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_multiple_keywords(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "multiple_keywords",
            {"keywords": "machine learning genomics", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 2. DOI lookup
# ===================================================================

class TestDOILookup:
    """Retrieve publications by DOI."""

    def test_single_doi(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "single_doi",
            {"doi": "10.1038/s41586-020-2649-2", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_multiple_dois(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "multiple_dois",
            {
                "doi": "10.1038/s41586-020-2649-2,10.1126/science.abc4730",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 3. ORCID-based search
# ===================================================================

class TestORCIDSearch:
    """Search publications linked to a given ORCID iD."""

    def test_orcid(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "orcid",
            {"orcid": "0000-0002-9079-593X", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 4. Title search
# ===================================================================

class TestTitleSearch:
    """Search by title keywords."""

    def test_title(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "title",
            {"title": "deep learning protein structure", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 5. Author search
# ===================================================================

class TestAuthorSearch:
    """Search by author name."""

    def test_author(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "author",
            {"author": "John Smith", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 6. Date range filtering
# ===================================================================

class TestDateRange:
    """Filter publications by date of acceptance range."""

    def test_from_date(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "from_date",
            {
                "keywords": "climate change",
                "fromDateAccepted": "2023-01-01",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_date_range(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "date_range",
            {
                "keywords": "renewable energy",
                "fromDateAccepted": "2022-01-01",
                "toDateAccepted": "2022-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 7. Open Access filtering
# ===================================================================

class TestOpenAccess:
    """Filter by Open Access status."""

    def test_open_access_true(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "open_access_true",
            {"keywords": "quantum computing", "OA": "true", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_open_access_false(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "open_access_false",
            {"keywords": "quantum computing", "OA": "false", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 8. Funder filtering
# ===================================================================

class TestFunderFiltering:
    """Filter by funder and EC funding."""

    def test_funder_ec(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "funder_ec",
            {"funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_funder_nsf(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "funder_nsf",
            {"funder": "NSF", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_has_ec_funding_true(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "has_ec_funding_true",
            {"hasECFunding": "true", "keywords": "graphene", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_has_wt_funding(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "has_wt_funding",
            {"hasWTFunding": "true", "keywords": "malaria", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 9. Country filtering
# ===================================================================

class TestCountryFiltering:
    """Filter by country code."""

    def test_country_de(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "country_de",
            {"country": "DE", "keywords": "biodiversity", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_country_gb(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "country_gb",
            {"country": "GB", "keywords": "artificial intelligence", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 10. Sorting
# ===================================================================

class TestSorting:
    """Verify sorted result ordering is preserved."""

    def test_sort_by_date_descending(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "sort_by_date_descending",
            {
                "keywords": "CRISPR",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_sort_by_date_ascending(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "sort_by_date_ascending",
            {
                "keywords": "CRISPR",
                "sortBy": "resultdateofacceptance,ascending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 11. Pagination
# ===================================================================

class TestPagination:
    """Ensure pagination returns consistent slices."""

    def test_page_1(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "page_1",
            {"keywords": "nanotechnology", "size": "5", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_page_2(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "page_2",
            {"keywords": "nanotechnology", "size": "5", "page": "2"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_large_page_size(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "large_page_size",
            {"keywords": "nanotechnology", "size": "50", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 12. Peer-reviewed publications
# ===================================================================

class TestPeerReviewed:
    """Filter by peer-review status (publication-specific parameter)."""

    def test_peer_reviewed_true(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "peer_reviewed_true",
            {"peerReviewed": "true", "keywords": "gene therapy", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_peer_reviewed_false(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "peer_reviewed_false",
            {"peerReviewed": "false", "keywords": "gene therapy", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 13. Diamond journal
# ===================================================================

class TestDiamondJournal:
    """Filter for publications in diamond OA journals."""

    def test_diamond_journal(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "diamond_journal",
            {"diamondJournal": "true", "keywords": "ecology", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 14. Publicly funded
# ===================================================================

class TestPubliclyFunded:
    """Filter for publicly funded publications."""

    def test_publicly_funded(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "publicly_funded",
            {"publiclyFunded": "true", "keywords": "vaccine", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 15. Green Open Access
# ===================================================================

class TestGreenOA:
    """Filter by green OA status."""

    def test_green_true(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "green_true",
            {"green": "true", "keywords": "neuroscience", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 16. Open Access colour
# ===================================================================

class TestOAColor:
    """Filter by open access colour (gold, bronze, hybrid)."""

    def test_gold(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "gold",
            {"openAccessColor": "gold", "keywords": "cancer", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_hybrid(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "hybrid",
            {"openAccessColor": "hybrid", "keywords": "cancer", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 17. Sustainable Development Goals (SDG)
# ===================================================================

class TestSDG:
    """Filter by SDG classification number."""

    def test_sdg_3_health(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "sdg_3_health",
            {"sdg": "3", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_sdg_13_climate(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "sdg_13_climate",
            {"sdg": "13", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 18. Field of Science (FOS)
# ===================================================================

class TestFieldOfScience:
    """Filter by Field of Science classification."""

    def test_fos(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "fos",
            {"fos": "Computer and information sciences", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 19. Influence / Popularity / Citation Count / Impulse
# ===================================================================

class TestImpactIndicators:
    """Filter by bibliometric impact indicators."""

    def test_influence_c1(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "influence_c1",
            {"influence": "C1", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_popularity_c2(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "popularity_c2",
            {"popularity": "C2", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_citation_count_c3(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "citation_count_c3",
            {"citationCount": "C3", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_impulse_c1(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "impulse_c1",
            {"impulse": "C1", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 20. OpenAIRE Publication ID
# ===================================================================

class TestOpenairePublicationID:
    """Look up a specific publication by its OpenAIRE identifier."""

    def test_openaire_id(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "openaire_id",
            {
                "openairePublicationID": "doi_dedup___::b91639a733694c00946368b7bb76a70f",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 21. Project-linked publications
# ===================================================================

class TestProjectLinked:
    """Search for publications linked to projects."""

    def test_has_project_true(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "has_project_true",
            {"hasProject": "true", "keywords": "higgs boson", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_fp7_project_id(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "fp7_project_id",
            {"FP7ProjectID": "283595", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 22. Provider filtering
# ===================================================================

class TestProviderFiltering:
    """Filter by data provider identifier."""

    def test_provider(self, base_url, endpoint, snapshot_dir_publications, phase):
        # Using the OpenAIRE provider ID for Zenodo
        _run_test(
            "provider",
            {
                "openaireProviderID": "opendoar____::358aee4cc897452c00244351e4d91f69",
                "keywords": "software",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )


# ===================================================================
# 23. Response format – JSON
# ===================================================================

class TestJSONFormat:
    """Verify that JSON responses maintain the same contract."""

    def test_json_keyword_search(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "json_keyword_search",
            {"keywords": "blockchain", "size": "10", "page": "1"},
            base_url, endpoint, snapshot_dir_publications, phase,
            fmt="json",
        )


# ===================================================================
# 24. Combined filters
# ===================================================================

class TestCombinedFilters:
    """Test queries that combine multiple filter parameters."""

    def test_keyword_oa_country_date(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "keyword_oa_country_date",
            {
                "keywords": "robotics",
                "OA": "true",
                "country": "IT",
                "fromDateAccepted": "2021-01-01",
                "toDateAccepted": "2023-12-31",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_funder_peer_reviewed_sorted(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "funder_peer_reviewed_sorted",
            {
                "funder": "EC",
                "peerReviewed": "true",
                "keywords": "sustainability",
                "sortBy": "resultdateofacceptance,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_sdg_green_diamond(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "sdg_green_diamond",
            {
                "sdg": "7",
                "green": "true",
                "diamondJournal": "true",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )

    def test_influence_oa_color_country(self, base_url, endpoint, snapshot_dir_publications, phase):
        _run_test(
            "influence_oa_color_country",
            {
                "influence": "C1",
                "openAccessColor": "gold",
                "country": "US",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint, snapshot_dir_publications, phase,
        )

"""
OpenAIRE Search Projects API – Contract Test Suite
====================================================

Exercises the ``/search/projects`` endpoint whose metadata schema differs
from the research-product endpoints (publications, datasets, software, other).
Projects expose fields such as grant ID (``code``), ``acronym``,
``startdate`` / ``enddate``, ``funder``, etc.

Documentation:
  https://graph.openaire.eu/docs/apis/search-api/projects

Modes
-----
* ``--phase=record``  – call the API and persist the normalised response as a
  baseline snapshot.
* ``--phase=compare`` – call the API, normalise, and assert equivalence with
  the stored baseline.

Run with::

    pytest test_projects_contract.py --phase=record -v
    pytest test_projects_contract.py --phase=compare -v
"""

import os

import pytest

from helpers import (
    DEFAULT_TOTAL_TOLERANCE_PCT,
    query_api,
    normalise_project_json_response,
    normalise_project_xml_response,
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
    Core test driver for the projects endpoint.

    Uses project-specific normalisers and loose comparison by default.
    """
    status, body, request_url, response_time_ms = query_api(base_url, endpoint, params, fmt=fmt)
    assert status == 200, f"Expected HTTP 200, got {status}\n  URL: {request_url}"

    if fmt == "json":
        current = normalise_project_json_response(body)
    else:
        current = normalise_project_xml_response(body)

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
            + "\n".join(f"  • {d}" for d in diffs)
        )


# ===================================================================
# 1. Keyword search
# ===================================================================

class TestKeywordSearch:
    """Search projects by keywords."""

    def test_single_keyword(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "single_keyword",
            {"keywords": "health", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_multiple_keywords(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "multiple_keywords",
            {"keywords": "renewable energy transition", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 2. Grant ID lookup
# ===================================================================

class TestGrantIDLookup:
    """Retrieve projects by grant ID."""

    def test_grant_id(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "grant_id",
            {"grantID": "283595", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
            loose=False,
        )


# ===================================================================
# 3. Project name search
# ===================================================================

class TestNameSearch:
    """Search projects by name."""

    def test_name(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "name",
            {"name": "Open Science", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 4. Acronym search
# ===================================================================

class TestAcronymSearch:
    """Search project by acronym."""

    def test_acronym(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "acronym",
            {"acronym": "OpenAIRE", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
            loose=False,
        )


# ===================================================================
# 5. Funder filtering
# ===================================================================

class TestFunderFiltering:
    """Filter projects by funder."""

    def test_funder_ec(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "funder_ec",
            {"funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_funder_nsf(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "funder_nsf",
            {"funder": "NSF", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_funder_wt(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "funder_wt",
            {"funder": "WT", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_has_ec_funding_true(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "has_ec_funding_true",
            {"hasECFunding": "true", "keywords": "innovation", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_has_wt_funding_true(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "has_wt_funding_true",
            {"hasWTFunding": "true", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 6. Call ID filtering
# ===================================================================

class TestCallID:
    """Filter projects by call identifier."""

    def test_call_id(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "call_id",
            {"callID": "H2020-MSCA-IF-2014", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 7. Start / End year filtering
# ===================================================================

class TestYearFiltering:
    """Filter projects by start or end year."""

    def test_start_year(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "start_year",
            {"startYear": "2020", "funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_end_year(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "end_year",
            {"endYear": "2023", "funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 8. Participant countries
# ===================================================================

class TestParticipantCountries:
    """Filter projects by participant countries."""

    def test_participant_country_de(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "participant_country_de",
            {"participantCountries": "DE", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_participant_country_fr(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "participant_country_fr",
            {"participantCountries": "FR", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 9. Participant acronyms (institutions)
# ===================================================================

class TestParticipantAcronyms:
    """Filter projects by participant institution acronyms."""

    def test_participant_acronym(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "participant_acronym",
            {"participantAcronyms": "CERN", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 10. Sorting
# ===================================================================

class TestSorting:
    """Verify sorted result ordering is preserved for projects."""

    def test_sort_by_start_date_desc(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "sort_by_start_date_desc",
            {
                "keywords": "climate",
                "sortBy": "projectstartdate,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_sort_by_start_date_asc(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "sort_by_start_date_asc",
            {
                "keywords": "climate",
                "sortBy": "projectstartdate,ascending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_sort_by_end_date_desc(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "sort_by_end_date_desc",
            {
                "keywords": "climate",
                "sortBy": "projectenddate,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 11. Pagination
# ===================================================================

class TestPagination:
    """Ensure pagination returns consistent slices."""

    def test_page_1(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "page_1",
            {"keywords": "digital", "funder": "EC", "size": "5", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_page_2(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "page_2",
            {"keywords": "digital", "funder": "EC", "size": "5", "page": "2"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_large_page_size(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "large_page_size",
            {"keywords": "digital", "funder": "EC", "size": "50", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 12. FP7 scientific area
# ===================================================================

class TestFP7ScientificArea:
    """Filter FP7 projects by scientific area."""

    def test_fp7_scientific_area(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "fp7_scientific_area",
            {"FP7scientificArea": "health", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 13. Funding stream
# ===================================================================

class TestFundingStream:
    """Filter projects by funding stream."""

    def test_funding_stream(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "funding_stream",
            {"fundingStream": "H2020", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )


# ===================================================================
# 14. XML format
# ===================================================================

class TestJSONFormat:
    """Verify that JSON responses maintain the same contract."""

    def test_json_keyword_search(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "json_keyword_search",
            {"keywords": "artificial intelligence", "funder": "EC", "size": "10", "page": "1"},
            base_url, endpoint_projects, snapshot_dir_projects, phase,
            fmt="json",
        )


# ===================================================================
# 15. Combined filters
# ===================================================================

class TestCombinedFilters:
    """Test queries that combine multiple filter parameters for projects."""

    def test_funder_country_year(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "funder_country_year",
            {
                "funder": "EC",
                "participantCountries": "DE",
                "startYear": "2020",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_keywords_funder_sorted(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "keywords_funder_sorted",
            {
                "keywords": "sustainability",
                "funder": "EC",
                "sortBy": "projectstartdate,descending",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

    def test_funder_call_country(self, base_url, endpoint_projects, snapshot_dir_projects, phase):
        _run_test(
            "funder_call_country",
            {
                "funder": "EC",
                "callID": "H2020-MSCA-IF-2014",
                "participantCountries": "IT",
                "size": "10",
                "page": "1",
            },
            base_url, endpoint_projects, snapshot_dir_projects, phase,
        )

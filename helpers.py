"""
Shared helpers for querying the OpenAIRE Search API, normalising responses,
and persisting / loading snapshots.

Supports research-product endpoints (publications, datasets, software, other)
as well as the project-specific endpoint with its distinct metadata schema.
"""

import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from lxml import etree

# ---------------------------------------------------------------------------
# Configuration defaults (overridable via environment)
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = int(os.environ.get("OPENAIRE_REQUEST_TIMEOUT", "60"))
RETRY_COUNT = int(os.environ.get("OPENAIRE_RETRY_COUNT", "3"))
RETRY_DELAY = int(os.environ.get("OPENAIRE_RETRY_DELAY", "5"))

# Default tolerance (%) for total-count comparison in multi-result queries.
# The indexes behind different API instances may differ slightly, so we allow
# a small deviation by default.
DEFAULT_TOTAL_TOLERANCE_PCT = 10.0

# Metadata fields we consider relevant for contract comparison.
# Anything not listed here is ignored during diff so that volatile fields
# (e.g. dateofcollection) do not cause false failures.
COMPARABLE_FIELDS = (
    "objectIdentifier",
    "objectType",
    "title",
    "dateofacceptance",
    "publisher",
    "bestaccessright",
    "creator",
    "doi",
)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _build_session() -> requests.Session:
    s = requests.Session()
    return s


def query_api(
    base_url: str,
    path: str,
    params: Dict[str, Any],
    *,
    fmt: str = "json",
) -> Tuple[int, Any, str]:
    """
    Query the OpenAIRE Search API.

    Returns (http_status_code, parsed_body, request_url).
    For ``fmt="json"`` the body is a Python dict; for ``fmt="xml"`` it is the
    raw XML text so that we can compare it structurally.
    ``request_url`` is the full URL with query parameters as sent to the server.
    """
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    merged = {**params, "format": fmt}

    session = _build_session()
    last_exc: Optional[Exception] = None

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = session.get(url, params=merged, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY * attempt)
                continue
            if fmt == "json":
                return resp.status_code, resp.json(), resp.url
            else:
                return resp.status_code, resp.text, resp.url
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY * attempt)

    raise RuntimeError(
        f"API request failed after {RETRY_COUNT} attempts: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Response normalisation
# ---------------------------------------------------------------------------

def _safe_text(element, tag: str) -> Optional[str]:
    """Extract text from a child element, or None."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _extract_creators(result_element) -> List[str]:
    """Return a sorted list of creator full-names."""
    creators = []
    for c in result_element.findall(".//creator"):
        if c.text:
            creators.append(c.text.strip())
    return sorted(creators)


def _extract_dois(result_element) -> List[str]:
    """Return sorted DOIs from pid elements."""
    dois = []
    for pid in result_element.findall(".//pid"):
        classid = pid.get("classid", "")
        if classid.lower() == "doi" and pid.text:
            dois.append(pid.text.strip().lower())
    return sorted(dois)


def normalise_json_response(body: dict) -> dict:
    """
    Distil a JSON API response down to the fields we care about for
    contract comparison.

    Returns a dict with:
      - ``total``: total number of results reported
      - ``page``, ``size``: pagination info echoed back
      - ``results``: list of normalised result dicts
    """
    response = body.get("response", body)
    header = response.get("header", {})
    total = int(header.get("total", {}).get("$", 0)) if isinstance(header.get("total"), dict) else int(header.get("total", 0))
    page_info = header.get("page", {})
    if isinstance(page_info, dict):
        page_num = page_info.get("$", None)
        page_size = page_info.get("@size", None)
    else:
        page_num = None
        page_size = None

    results_wrapper = response.get("results") or {}
    raw_results = results_wrapper.get("result") or []
    if isinstance(raw_results, dict):
        raw_results = [raw_results]

    normalised = []
    for r in raw_results:
        metadata = r.get("metadata", {})
        entity = metadata.get("oaf:entity", metadata)
        result = entity.get("oaf:result", entity)

        # Extract title -- may be a list or a single dict/str
        title_raw = result.get("title", "")
        if isinstance(title_raw, list):
            title = title_raw[0].get("$", str(title_raw[0])) if title_raw else ""
        elif isinstance(title_raw, dict):
            title = title_raw.get("$", str(title_raw))
        else:
            title = str(title_raw)

        # objectIdentifier
        obj_id = r.get("header", {}).get("dri:objIdentifier", {})
        if isinstance(obj_id, dict):
            obj_id = obj_id.get("$", "")

        # dateofacceptance
        doa = result.get("dateofacceptance", "")
        if isinstance(doa, dict):
            doa = doa.get("$", "")

        # bestaccessright
        bar = result.get("bestaccessright", "")
        if isinstance(bar, dict):
            bar = bar.get("@classid", bar.get("$", ""))

        # publisher
        pub = result.get("publisher", "")
        if isinstance(pub, dict):
            pub = pub.get("$", "")

        # creators
        creators_raw = result.get("creator", [])
        if isinstance(creators_raw, dict):
            creators_raw = [creators_raw]
        creators = sorted(
            c.get("$", str(c)) if isinstance(c, dict) else str(c)
            for c in creators_raw
        )

        # DOIs from pid
        pid_raw = result.get("pid", [])
        if isinstance(pid_raw, dict):
            pid_raw = [pid_raw]
        dois = sorted(
            p.get("$", "").strip().lower()
            for p in pid_raw
            if isinstance(p, dict) and p.get("@classid", "").lower() == "doi" and p.get("$")
        )

        normalised.append({
            "objectIdentifier": obj_id,
            "title": title,
            "dateofacceptance": doa,
            "bestaccessright": bar,
            "publisher": pub,
            "creators": creators,
            "dois": dois,
        })

    return {
        "total": total,
        "page": page_num,
        "size": page_size,
        "results": normalised,
    }


def normalise_xml_response(xml_text: str) -> dict:
    """
    Parse an XML response and extract the same contract-relevant fields as
    the JSON normaliser.
    """
    root = etree.fromstring(xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text)

    # Total
    header = root.find(".//header")
    total_el = header.find("total") if header is not None else None
    total = int(total_el.text) if total_el is not None and total_el.text else 0

    page_el = header.find("page") if header is not None else None
    page_num = page_el.text if page_el is not None and page_el.text else None
    page_size = page_el.get("size") if page_el is not None else None

    results = []
    for res in root.findall(".//result"):
        obj_id_el = res.find(".//dri:objIdentifier", namespaces={
            "dri": "http://www.driver-repository.eu/namespace/dri"
        })
        # Fallback: try without namespace
        if obj_id_el is None:
            obj_id_el = res.find("./header/objIdentifier")
        obj_id = obj_id_el.text.strip() if obj_id_el is not None and obj_id_el.text else ""

        # Navigate into oaf:result
        oaf_result = res.find(".//{http://namespace.openaire.eu/oaf}result")
        if oaf_result is None:
            oaf_result = res

        title_el = oaf_result.find("title")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        doa_el = oaf_result.find("dateofacceptance")
        doa = doa_el.text.strip() if doa_el is not None and doa_el.text else ""

        bar_el = oaf_result.find("bestaccessright")
        bar = bar_el.get("classid", bar_el.text.strip() if bar_el is not None and bar_el.text else "") if bar_el is not None else ""

        pub_el = oaf_result.find("publisher")
        pub = pub_el.text.strip() if pub_el is not None and pub_el.text else ""

        creators = sorted(
            c.text.strip()
            for c in oaf_result.findall("creator")
            if c.text
        )

        dois = sorted(
            p.text.strip().lower()
            for p in oaf_result.findall("pid")
            if p.get("classid", "").lower() == "doi" and p.text
        )

        results.append({
            "objectIdentifier": obj_id,
            "title": title,
            "dateofacceptance": doa,
            "bestaccessright": bar,
            "publisher": pub,
            "creators": creators,
            "dois": dois,
        })

    return {
        "total": total,
        "page": page_num,
        "size": page_size,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Project-specific normalisation
# ---------------------------------------------------------------------------

def normalise_project_json_response(body: dict) -> dict:
    """
    Distil a JSON API response from the projects endpoint down to the
    contract-relevant fields.

    Projects have a different metadata schema (``oaf:project`` instead of
    ``oaf:result``) with fields like code (grant ID), acronym, title,
    start/end dates, funder, etc.
    """
    response = body.get("response", body)
    header = response.get("header", {})
    total = (
        int(header.get("total", {}).get("$", 0))
        if isinstance(header.get("total"), dict)
        else int(header.get("total", 0))
    )
    page_info = header.get("page", {})
    if isinstance(page_info, dict):
        page_num = page_info.get("$", None)
        page_size = page_info.get("@size", None)
    else:
        page_num = None
        page_size = None

    results_wrapper = response.get("results") or {}
    raw_results = results_wrapper.get("result") or []
    if isinstance(raw_results, dict):
        raw_results = [raw_results]

    normalised = []
    for r in raw_results:
        metadata = r.get("metadata", {})
        entity = metadata.get("oaf:entity", metadata)
        project = entity.get("oaf:project", entity)

        # objectIdentifier
        obj_id = r.get("header", {}).get("dri:objIdentifier", {})
        if isinstance(obj_id, dict):
            obj_id = obj_id.get("$", "")

        # code (grant ID)
        code = project.get("code", "")
        if isinstance(code, dict):
            code = code.get("$", "")

        # title
        title_raw = project.get("title", "")
        if isinstance(title_raw, dict):
            title = title_raw.get("$", str(title_raw))
        else:
            title = str(title_raw)

        # acronym
        acronym = project.get("acronym", "")
        if isinstance(acronym, dict):
            acronym = acronym.get("$", "")

        # startdate / enddate
        startdate = project.get("startdate", "")
        if isinstance(startdate, dict):
            startdate = startdate.get("$", "")
        enddate = project.get("enddate", "")
        if isinstance(enddate, dict):
            enddate = enddate.get("$", "")

        # fundingtree → funder name
        funder_name = ""
        ft = project.get("fundingtree", {})
        if isinstance(ft, list):
            ft = ft[0] if ft else {}
        if isinstance(ft, dict):
            funder = ft.get("funder", {})
            if isinstance(funder, dict):
                fn = funder.get("name", "")
                funder_name = fn.get("$", str(fn)) if isinstance(fn, dict) else str(fn)

        normalised.append({
            "objectIdentifier": obj_id,
            "code": code,
            "title": title,
            "acronym": acronym,
            "startdate": startdate,
            "enddate": enddate,
            "funder": funder_name,
        })

    return {
        "total": total,
        "page": page_num,
        "size": page_size,
        "results": normalised,
    }


def normalise_project_xml_response(xml_text: str) -> dict:
    """
    Parse an XML response from the projects endpoint and extract contract-
    relevant project fields.
    """
    root = etree.fromstring(
        xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text
    )

    header = root.find(".//header")
    total_el = header.find("total") if header is not None else None
    total = int(total_el.text) if total_el is not None and total_el.text else 0

    page_el = header.find("page") if header is not None else None
    page_num = page_el.text if page_el is not None and page_el.text else None
    page_size = page_el.get("size") if page_el is not None else None

    results = []
    for res in root.findall(".//result"):
        obj_id_el = res.find(
            ".//dri:objIdentifier",
            namespaces={"dri": "http://www.driver-repository.eu/namespace/dri"},
        )
        if obj_id_el is None:
            obj_id_el = res.find("./header/objIdentifier")
        obj_id = obj_id_el.text.strip() if obj_id_el is not None and obj_id_el.text else ""

        oaf_project = res.find(".//{http://namespace.openaire.eu/oaf}project")
        if oaf_project is None:
            oaf_project = res

        def _txt(parent, tag):
            el = parent.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        code = _txt(oaf_project, "code")
        title = _txt(oaf_project, "title")
        acronym = _txt(oaf_project, "acronym")
        startdate = _txt(oaf_project, "startdate")
        enddate = _txt(oaf_project, "enddate")

        funder_el = oaf_project.find(".//funder")
        funder_name = ""
        if funder_el is not None:
            name_el = funder_el.find("name")
            funder_name = name_el.text.strip() if name_el is not None and name_el.text else ""

        results.append({
            "objectIdentifier": obj_id,
            "code": code,
            "title": title,
            "acronym": acronym,
            "startdate": startdate,
            "enddate": enddate,
            "funder": funder_name,
        })

    return {
        "total": total,
        "page": page_num,
        "size": page_size,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------

def _snapshot_path(snapshot_dir: str, test_id: str) -> str:
    """Deterministic file-path for a test case snapshot."""
    safe = test_id.replace("/", "_").replace("::", "__")
    return os.path.join(snapshot_dir, f"{safe}.json")


def save_snapshot(snapshot_dir: str, test_id: str, *, params: dict, normalised: dict):
    path = _snapshot_path(snapshot_dir, test_id)
    payload = {"params": params, "normalised": normalised}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)


def load_snapshot(snapshot_dir: str, test_id: str) -> dict:
    path = _snapshot_path(snapshot_dir, test_id)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No baseline snapshot found at {path}. "
            "Run `pytest --phase=record` first to create baselines."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def compare_snapshots(
    baseline: dict,
    current: dict,
    *,
    total_tolerance_pct: float = 0.0,
    loose: bool = False,
) -> List[str]:
    """
    Compare two normalised response dicts.

    Returns a list of human-readable difference descriptions.
    An empty list means the responses are equivalent.

    ``total_tolerance_pct`` allows the total result count to differ by up to
    this percentage (useful for huge result sets where minor index changes
    are acceptable).  Set to 0.0 for exact match.

    ``loose``  – when True the comparison is relaxed:
      * The number of results on the page may differ.
      * Result ordering is not checked.
      * Instead of a positional field-by-field diff we check that the *set* of
        object identifiers from the baseline overlaps with the current result
        set by at least 50 %.  This accounts for minor index churn across
        different backend instances while still catching wholesale breakage.
    """
    diffs: List[str] = []

    # 1. Total count
    bt, ct = baseline["total"], current["total"]
    if bt != ct:
        if bt == 0 or abs(ct - bt) / bt * 100 > total_tolerance_pct:
            diffs.append(f"Total count changed: baseline={bt}, current={ct}")

    # 2. Results list
    b_results = baseline["results"]
    c_results = current["results"]

    if loose:
        # --- Loose comparison mode ---
        # We only verify that a reasonable proportion of baseline IDs are
        # still present and that result count hasn't changed wildly.
        if len(b_results) > 0 and len(c_results) == 0:
            diffs.append(
                "Current response returned 0 results on page but baseline "
                f"had {len(b_results)}."
            )
        elif len(b_results) > 0:
            b_ids = {r.get("objectIdentifier", "") for r in b_results} - {""}
            c_ids = {r.get("objectIdentifier", "") for r in c_results} - {""}
            if b_ids:
                overlap = b_ids & c_ids
                overlap_pct = len(overlap) / len(b_ids) * 100
                if overlap_pct < 50:
                    diffs.append(
                        f"Result-set overlap too low: only {overlap_pct:.0f}% of "
                        f"baseline IDs found in current results "
                        f"(baseline={len(b_ids)}, overlap={len(overlap)})."
                    )
    else:
        # --- Strict comparison mode ---
        if len(b_results) != len(c_results):
            diffs.append(
                f"Number of results on page differs: baseline={len(b_results)}, "
                f"current={len(c_results)}"
            )

        # Determine which fields to compare based on result structure
        # (projects have different keys than research products).
        sample = b_results[0] if b_results else {}
        if "code" in sample:
            # Project results
            scalar_keys = ("objectIdentifier", "code", "title", "acronym",
                           "startdate", "enddate", "funder")
            list_keys: tuple = ()
        else:
            # Research product results
            scalar_keys = ("objectIdentifier", "title", "dateofacceptance",
                           "bestaccessright", "publisher")
            list_keys = ("creators", "dois")

        for idx, (br, cr) in enumerate(zip(b_results, c_results)):
            for key in scalar_keys:
                bv = br.get(key, "")
                cv = cr.get(key, "")
                if bv != cv:
                    diffs.append(
                        f"Result[{idx}].{key} differs: "
                        f"baseline={bv!r}, current={cv!r}"
                    )
            for key in list_keys:
                if br.get(key) != cr.get(key):
                    diffs.append(
                        f"Result[{idx}].{key} differs: "
                        f"baseline={br.get(key)}, current={cr.get(key)}"
                    )

        # Check ordering by objectIdentifier
        b_ids = [r["objectIdentifier"] for r in b_results]
        c_ids = [r["objectIdentifier"] for r in c_results[:len(b_ids)]]
        if b_ids != c_ids:
            diffs.append(
                "Result ordering (by objectIdentifier) differs between baseline and current."
            )

    return diffs

"""
pytest configuration – adds the ``--phase`` CLI option and shared fixtures.

Provides per-endpoint snapshot directories so that responses from different
API endpoints (publications, datasets, software, other, projects) are stored
in isolated folders and never mixed.
"""

import os
import pytest

PHASE_CHOICES = ("record", "compare")

# Mapping from endpoint path suffix to default snapshot sub-directory name.
_ENDPOINT_SNAPSHOT_DIRS = {
    "search/publications": "snapshots_publications",
    "search/datasets": "snapshots_datasets",
    "search/software": "snapshots_software",
    "search/other": "snapshots_other",
    "search/projects": "snapshots_projects",
}


def pytest_addoption(parser):
    parser.addoption(
        "--phase",
        action="store",
        default="record",
        choices=PHASE_CHOICES,
        help="Phase of contract testing: 'record' saves baseline snapshots, "
             "'compare' checks current responses against stored snapshots.",
    )
    parser.addoption(
        "--snapshot-dir",
        action="store",
        default=None,
        help="Override the root snapshot directory (default: env OPENAIRE_SNAPSHOT_DIR or auto per-endpoint).",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Override the API base URL (default: env OPENAIRE_API_BASE_URL or 'https://api.openaire.eu').",
    )
    parser.addoption(
        "--endpoint",
        action="store",
        default=None,
        help="Override the endpoint path (default: env OPENAIRE_ENDPOINT or 'search/publications').",
    )


@pytest.fixture(scope="session")
def phase(request):
    return request.config.getoption("--phase")


def _resolve_snapshot_dir(request, endpoint_path: str) -> str:
    """
    Return the snapshot directory for a given endpoint.

    Priority:
      1. ``--snapshot-dir`` CLI option
      2. ``OPENAIRE_SNAPSHOT_DIR`` environment variable
      3. Auto-generated per-endpoint sub-directory under the project root
    """
    explicit = (
        request.config.getoption("--snapshot-dir")
        or os.environ.get("OPENAIRE_SNAPSHOT_DIR")
    )
    if explicit:
        d = explicit
    else:
        subdir = _ENDPOINT_SNAPSHOT_DIRS.get(
            endpoint_path,
            f"snapshots_{endpoint_path.replace('/', '_')}",
        )
        d = os.path.join(os.path.dirname(__file__), subdir)
    os.makedirs(d, exist_ok=True)
    return d


@pytest.fixture(scope="session")
def snapshot_dir(request):
    """Snapshot dir for the publications endpoint (legacy / default)."""
    return _resolve_snapshot_dir(request, "search/publications")


@pytest.fixture(scope="session")
def snapshot_dir_publications(request):
    return _resolve_snapshot_dir(request, "search/publications")


@pytest.fixture(scope="session")
def snapshot_dir_datasets(request):
    return _resolve_snapshot_dir(request, "search/datasets")


@pytest.fixture(scope="session")
def snapshot_dir_software(request):
    return _resolve_snapshot_dir(request, "search/software")


@pytest.fixture(scope="session")
def snapshot_dir_other(request):
    return _resolve_snapshot_dir(request, "search/other")


@pytest.fixture(scope="session")
def snapshot_dir_projects(request):
    return _resolve_snapshot_dir(request, "search/projects")


@pytest.fixture(scope="session")
def base_url(request):
    return (
        request.config.getoption("--base-url")
        or os.environ.get("OPENAIRE_API_BASE_URL")
        or "https://api.openaire.eu"
    )


@pytest.fixture(scope="session")
def endpoint(request):
    return (
        request.config.getoption("--endpoint")
        or os.environ.get("OPENAIRE_ENDPOINT")
        or "search/publications"
    )

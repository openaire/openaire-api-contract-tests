"""
pytest configuration – adds the ``--phase`` CLI option and shared fixtures.
"""

import os
import pytest

PHASE_CHOICES = ("record", "compare")


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
        help="Override the snapshot directory (default: env OPENAIRE_SNAPSHOT_DIR or 'snapshots').",
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


@pytest.fixture(scope="session")
def snapshot_dir(request):
    d = (
        request.config.getoption("--snapshot-dir")
        or os.environ.get("OPENAIRE_SNAPSHOT_DIR")
        or os.path.join(os.path.dirname(__file__), "snapshots")
    )
    os.makedirs(d, exist_ok=True)
    return d


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

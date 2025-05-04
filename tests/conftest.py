import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def pytest_addoption(parser):
    parser.addoption(
        "--url",
        action="store",
        default="http://host.docker.internal:5000",
        help="URL To Test",
    )


@pytest.fixture(scope="session")
def url_base(pytestconfig):
    return pytestconfig.getoption("url")

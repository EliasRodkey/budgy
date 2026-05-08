#!python3
import os

import pytest

from backend import logging_handler_controller


def pytest_addoption(parser):
    parser.addoption("--run-description", default="", help="What changed in this run")


@pytest.fixture(scope="session")
def run_context(pytestconfig):
    return {
        "timestamp": logging_handler_controller.log_datetime_stamp,
        "description": pytestconfig.getoption("--run-description"),
        "model": os.environ.get("AI_MODEL", "claude-haiku-4-5-20251001"),
    }

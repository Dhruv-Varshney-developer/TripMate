import os
import sys

import pytest

from browser_use.logging_config import setup_logging

# Get the absolute path to the project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

setup_logging()


class OpenAIError(Exception):
    """Custom Exception to simulate a missing OPENAI_API_KEY."""
    pass


def pytest_runtest_call(item):
    """Xfail pytests that raise an OpenAIError because of a missing OPENAI_API_KEY."""
    try:
        item.runtest()
    except OpenAIError:
        pytest.xfail(f"Test {item.name} ignored due to a missing OPENAI_API_KEY.")

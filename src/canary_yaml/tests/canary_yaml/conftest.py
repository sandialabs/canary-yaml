# Copyright NTESS. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: MIT

import os

import _canary.config
import _canary.util.multiprocessing as mp
import pytest

mp.initialize()


@pytest.fixture(scope="function", autouse=True)
def config():
    env_copy = os.environ.copy()
    try:
        os.environ.pop("CONFIG_ENV_FILENAME", None)
        os.environ.pop("CANARYCFG64", None)
        os.environ["CANARY_DISABLE_KB"] = "1"
        _canary.config._config = _canary.config.config.Config()
        yield
    finally:
        os.environ.clear()
        os.environ.update(env_copy)

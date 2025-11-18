import os

import canary

from .generator import YAMLTestGenerator
from .generator import setup_yaml_test


@canary.hookimpl
def canary_testcase_generator(root: str, path: str | None) -> YAMLTestGenerator:
    if YAMLTestGenerator.matches(root if path is None else os.path.join(root, path)):
        return YAMLTestGenerator(root, path)


@canary.hookimpl
def canary_testcase_setup(case: canary.TestCase) -> None:
    return setup_yaml_test(case)


@canary.hookimpl
def canary_testcase_execution_policy(case: canary.TestCase) -> canary.ExecutionPolicy | None:
    if YAMLTestGenerator.matches(case.spec.file):
        return canary.SubprocessExecutionPolicy(["./runtest.sh"])
    return None

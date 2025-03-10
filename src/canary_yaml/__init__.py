from typing import Type

import canary

from .generator import YAMLTestGenerator


@canary.hookimpl
def canary_testcase_generator() -> Type[YAMLTestGenerator]:
    return YAMLTestGenerator

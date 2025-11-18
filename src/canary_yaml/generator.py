import io
import os
import re
from pathlib import Path
from itertools import product
from string import Template
from typing import Any

import canary
import yaml


class YAMLTestGenerator(canary.AbstractTestGenerator):
    """Define a YAML defined test case with the following schema:

    .. code-block:: yaml

       tests:

         str:
           description: str
           script: list[str]
           keywords: list[str]
           parameters: dict[str, list[float | int | str | None]]

    """

    @classmethod
    def matches(cls, path: str | Path) -> bool:
        """Is ``path`` a YAMLTestGenerator?"""
        path = Path(path)
        return re.match("test_.*\.yaml", path.name) is not None

    def lock(self, on_options: list[str] | None = None) -> list[canary.DraftSpec]:
        """Take the cartesian product of parameters and from each combination create a test case."""

        with open(self.file, "r") as fh:
            fd = yaml.safe_load(fh)

        specs: list[canary.DraftSpec] = []
        for name, details in fd["tests"].items():
            kwds = dict(
                file_root=Path(self.root),
                file_path=Path(self.path),
                family=name,
                keywords=details.get("keywords", []),
                attributes={"details": details.get("description"), "script": details["script"]},
            )

            if "parameters" not in details:
                spec = canary.DraftSpec(**kwds)
                specs.append(spec)
                continue

            parameters = details.get("parameters", {})
            keys = list(parameters.keys())
            for values in product(*parameters.values()):
                params = dict(zip(keys, values))
                spec = canary.DraftSpec(parameters=params, **kwds)
                specs.append(spec)
        return specs

    def describe(self, on_options: list[str] | None = None) -> str:
        cases = self.lock(on_options=on_options)
        file = io.StringIO()
        file.write(f"--- {self.name} ------------\n")
        file.write(f"File: {self.file}\n")
        file.write(f"{len(cases)} test cases:\n")
        canary.graph.print(cases, file=file)
        return file.getvalue()


def setup_yaml_test(case: canary.TestCase):
    sh = canary.filesystem.which("sh")
    script = case.attributes["script"]
    with case.workspace.openfile("runtest.sh", "w") as fh:
        fh.write(f"#!{sh}\n")
        fh.write(f"cd {case.workspace.dir}\n")
        fh.write("\n".join(script))
    canary.filesystem.set_executable(case.workspace.joinpath("runtest.sh"))

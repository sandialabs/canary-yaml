import io
import json
import os
from typing import IO
from typing import Any
from typing import Optional

import yaml
from _nvtest.abc import AbstractTestGenerator
from _nvtest.resource import ResourceHandler
from _nvtest.test.case import TestCase
from _nvtest.util import graph
from _nvtest.util.filesystem import set_executable
from _nvtest.util.filesystem import working_dir


class YamlTestFile(AbstractTestGenerator):

    def __init__(self, root: str, path: Optional[str] = None) -> None:
        super().__init__(root, path=path)
        self.load(open(self.file).read())

    @classmethod
    def matches(cls, path: str) -> bool:
        return path.endswith((".yml", ".yaml"))

    def load(self, file: IO[Any]) -> None:
        name, details = self.load_file(file)
        self.name = name
        self.script = details["script"]
        self.cases = details.get("cases")
        self.description = details.get("description")
        self.keywords = details.get("keywords", [])
        self.sources = {}
        if "copy" in details:
            self.sources.setdefault("copy", []).extend(details["copy"])
        if "link" in details:
            self.sources.setdefault("link", []).extend(details["link"])

    @staticmethod
    def load_file(file: IO[Any]) -> tuple[str, dict]:
        data = yaml.safe_load(file)
        if not isinstance(data, dict):
            raise ValueError(f"{file.name}: expected test data to be a dictionary")
        if len(data) != 1:
            raise ValueError(f"{file.name}: expected one (and only one) test case")
        # Further data validation here...
        name = next(iter(data))
        details = data[name]
        return name, details

    def lock(
        self,
        cpus: Optional[list[int]] = None,
        gpus: Optional[list[int]] = None,
        nodes: Optional[list[int]] = None,
        keyword_expr: Optional[str] = None,
        on_options: Optional[list[str]] = None,
        parameter_expr: Optional[str] = None,
        timeout: Optional[float] = None,
        owners: Optional[set[str]] = None,
        env_mods: Optional[dict[str, str]] = None,
    ) -> list[TestCase]:

        cases: list[YamlTestCase] = []
        dirname = os.path.dirname(self.file)
        with working_dir(dirname):
            sources: dict[str, list[tuple[str, str]]] = {}
            for action, files in self.sources.items():
                for file in files:
                    src = os.path.abspath(file)
                    dst = os.path.basename(src)
                    sources.setdefault(action, []).append((src, dst))
            if not self.cases:
                case = YamlTestCase(
                    file_root=self.root,
                    file_path=self.path,
                    family=self.name,
                    script=self.script,
                    sources=sources,
                    keywords=self.keywords,
                    description=self.description,
                )
                cases.append(case)
            else:
                for case in self.cases:
                    parameters = case.get("parameters", {})
                    case = YamlTestCase(
                        file_root=self.root,
                        file_path=self.path,
                        parameters=parameters,
                        family=self.name,
                        script=self.script,
                        sources=sources,
                        keywords=self.keywords,
                        description=self.description,
                    )
                    cases.append(case)
        return cases  # type: ignore

    def describe(
        self,
        keyword_expr: Optional[str] = None,
        on_options: Optional[list[str]] = None,
        parameter_expr: Optional[str] = None,
        rh: Optional[ResourceHandler] = None,
    ) -> str:
        rh = rh or ResourceHandler()
        cases = self.lock(
            cpus=rh["test:cpu_count"],
            gpus=rh["test:gpu_count"],
            nodes=rh["test:node_count"],
            on_options=on_options,
            keyword_expr=keyword_expr,
            parameter_expr=parameter_expr,
        )
        file = io.StringIO()
        file.write(f"--- {self.name} ------------\n")
        file.write(f"File: {self.file}\n")
        file.write(f"Description: {self.description}\n")
        file.write(f"Keywords: {', '.join(self.keywords)}\n")
        file.write(f"{len(cases)} test cases:\n")
        graph.print(cases, file=file)
        return file.getvalue()


class YamlTestCase(TestCase):
    def __init__(
        self,
        *,
        file_root: str,
        file_path: str,
        script: list[str],
        keywords: list[str],
        family: str,
        sources: dict[str, list[tuple[str, str]]],
        description: str,
        parameters: dict[str, Any],
        **kwds,
    ) -> None:
        super().__init__(
            file_root=file_root,
            file_path=file_path,
            family=family,
            sources=sources,
            parameters=parameters,
        )

        if keywords is not None:
            self.keywords = keywords

        self.launcher = "bash"
        self.exe = "test_script.sh"
        self.description = description
        self.script = script

    def setup(self, exec_root: str, copy_all_resources: bool = False) -> None:
        super().setup(exec_root, copy_all_resources=copy_all_resources)
        with working_dir(self.exec_dir):
            with open(self.exe, "w") as fh:
                fh.write("#!/usr/bin/env bash\n")
                fh.write("\n".join(self.script))
            set_executable(self.exe)

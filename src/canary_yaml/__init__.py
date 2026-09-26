import io
from itertools import product
from pathlib import Path
from string import Template
from typing import Any
from typing import ClassVar

import canary
import yaml

YamlCase = dict[str, Any]
YamlTests = dict[str, YamlCase]


@canary.hookimpl
def canary_collectstart(collector: Any) -> None:
    collector.add_generator(YAMLSpecGenerator)


class YAMLSpecGenerator(canary.AbstractSpecGenerator):
    """Generate Canary specs from YAML test files.

    Supported YAML format:

    .. code-block:: yaml

       tests:
         test_name:
           description: str
           script: list[str]
           keywords: list[str]
           parameters: dict[str, list[str | int | float | bool | None]]
    """

    file_patterns: ClassVar[tuple[str, ...]] = ("test_*.yaml", "test_*.yml")

    def lock(self, on_options: list[str] | None = None) -> list[canary.ResolvedSpec]:
        """Create one resolved spec for each YAML test and parameter combination."""
        del on_options

        tests = _load_tests(Path(self.file))
        sh = _shell_executable()

        specs: list[canary.ResolvedSpec] = []

        for family, details in tests.items():
            script: list[str] = details["script"]
            keywords: list[str] = details["keywords"]
            description: str = details["description"]
            parameters: dict[str, list[Any]] = details["parameters"]

            for parameter_values in _parameter_combinations(parameters):
                specs.append(
                    canary.ResolvedSpec(
                        file_root=Path(self.root),
                        file_path=Path(self.path),
                        family=family,
                        keywords=keywords,
                        attributes={"description": description},
                        parameters=parameter_values,
                        command=_command(sh, script, parameter_values),
                    )
                )

        return specs

    def describe(self, on_options: list[str] | None = None) -> str:
        cases = self.lock(on_options=on_options)

        keywords: list[str] = []
        for case in cases:
            for keyword in case.keywords:
                if keyword not in keywords:
                    keywords.append(keyword)

        file = io.StringIO()
        file.write(f"--- {Path(self.file).name} ------------\n")
        file.write(f"File: {self.file}\n")
        file.write(f"Keywords: {', '.join(keywords)}\n")
        file.write(f"{len(cases)} test specs:\n")

        for case in cases:
            file.write(f"  {case.family}")
            if case.parameters:
                file.write(f" {case.parameters}")
            file.write("\n")

        return file.getvalue()


def _shell_executable() -> str:
    return str(canary.filesystem.which("sh", required=True))


def _load_tests(file: Path) -> YamlTests:
    with open(file, encoding="utf-8") as fh:
        document = yaml.safe_load(fh)

    if document is None:
        document = {}

    if not isinstance(document, dict):
        raise ValueError(f"{file}: YAML document must be a mapping")

    if "tests" not in document:
        raise ValueError(f"{file}: missing required top-level 'tests' mapping")

    tests = document["tests"]
    if not isinstance(tests, dict):
        raise ValueError(f"{file}: 'tests' must be a mapping")

    return {
        family: _validate_test_details(file, family, details) for family, details in tests.items()
    }


def _validate_test_details(
    file: Path,
    family: Any,
    details: Any,
) -> YamlCase:
    if not isinstance(family, str) or not family:
        raise ValueError(f"{file}: test names must be non-empty strings")

    location = f"tests.{family}"

    if not isinstance(details, dict):
        raise ValueError(f"{file}: {location} must be a mapping")

    allowed_keys = {"description", "script", "keywords", "parameters"}
    extra_keys = sorted(set(details) - allowed_keys)
    if extra_keys:
        keys = ", ".join(str(key) for key in extra_keys)
        raise ValueError(f"{file}: {location} has unsupported key(s): {keys}")

    if "script" not in details:
        raise ValueError(f"{file}: {location}.script is required")

    script = details["script"]
    if not isinstance(script, list) or not all(isinstance(item, str) for item in script):
        raise ValueError(f"{file}: {location}.script must be a list of strings")

    description = details.get("description", "Yaml test instance")
    if not isinstance(description, str):
        raise ValueError(f"{file}: {location}.description must be a string")

    keywords = details.get("keywords", [])
    if not isinstance(keywords, list) or not all(isinstance(item, str) for item in keywords):
        raise ValueError(f"{file}: {location}.keywords must be a list of strings")

    parameters = details.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError(f"{file}: {location}.parameters must be a mapping")

    validated_parameters: dict[str, list[Any]] = {}

    for name, values in parameters.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"{file}: {location}.parameters keys must be non-empty strings")

        if not isinstance(values, list):
            raise ValueError(f"{file}: {location}.parameters.{name} must be a list")

        for value in values:
            if not _is_valid_parameter_value(value):
                raise ValueError(
                    f"{file}: {location}.parameters.{name} values must be "
                    "strings, integers, floats, booleans, or null"
                )

        validated_parameters[name] = list(values)

    return {
        "description": description,
        "script": list(script),
        "keywords": list(keywords),
        "parameters": validated_parameters,
    }


def _is_valid_parameter_value(value: Any) -> bool:
    return (
        value is None
        or isinstance(value, str)
        or isinstance(value, bool)
        or type(value) in {int, float}
    )


def _parameter_combinations(parameters: dict[str, list[Any]]) -> list[dict[str, Any]]:
    if not parameters:
        return [{}]

    names = list(parameters)
    values = [parameters[name] for name in names]

    return [dict(zip(names, combination)) for combination in product(*values)]


def _command(
    sh: str,
    script: list[str],
    parameters: dict[str, Any],
) -> list[str]:
    mapping = _template_mapping(parameters)
    shell_lines = [Template(line).safe_substitute(mapping) for line in script]
    return [sh, "-c", "set -e\n" + "\n".join(shell_lines)]


def _template_mapping(parameters: dict[str, Any]) -> dict[str, Any]:
    mapping = dict(parameters)

    for key, value in parameters.items():
        mapping.setdefault(key.upper(), value)

    return mapping

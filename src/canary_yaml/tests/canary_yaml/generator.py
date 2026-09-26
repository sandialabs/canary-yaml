# Copyright NTESS. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

import canary_yaml


def make_yaml_file(tmp_path: Path, rel: str, text: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def make_generator(
    tmp_path: Path,
    rel: str,
    text: str,
    monkeypatch: pytest.MonkeyPatch,
) -> canary_yaml.YAMLSpecGenerator:
    make_yaml_file(tmp_path, rel, text)

    monkeypatch.setattr(canary_yaml, "_shell_executable", lambda: "/bin/sh")

    return canary_yaml.YAMLSpecGenerator(str(tmp_path), rel)


def lock_yaml(
    tmp_path: Path,
    rel: str,
    text: str,
    monkeypatch: pytest.MonkeyPatch,
):
    gen = make_generator(tmp_path, rel, text, monkeypatch)
    return gen.lock()


from typing import Any


def test_collectstart_registers_yaml_generator() -> None:
    class Collector:
        def __init__(self) -> None:
            self.generators: list[Any] = []

        def add_generator(self, generator: Any) -> None:
            self.generators.append(generator)

    collector = Collector()

    canary_yaml.canary_collectstart(collector)

    assert collector.generators == [canary_yaml.YAMLSpecGenerator]


def test_yaml_generator_declares_file_patterns() -> None:
    assert canary_yaml.YAMLSpecGenerator.file_patterns == ("test_*.yaml", "test_*.yml")


def test_lock_no_parameters_produces_one_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = lock_yaml(
        tmp_path,
        "test_simple.yaml",
        """
tests:
  hello:
    description: "A simple YAML test"
    script:
      - echo hello
      - echo world
    keywords:
      - smoke
      - yaml
""",
        monkeypatch,
    )

    assert len(specs) == 1

    s = specs[0]
    assert s.file_root == tmp_path
    assert s.file_path == Path("test_simple.yaml")
    assert s.family == "hello"
    assert s.parameters == {}
    assert s.keywords == ["smoke", "yaml"]
    assert s.attributes["description"] == "A simple YAML test"
    assert s.command == ["/bin/sh", "-c", "set -e\necho hello\necho world"]


def test_lock_defaults_description_keywords_and_parameters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = lock_yaml(
        tmp_path,
        "test_defaults.yaml",
        """
tests:
  defaults:
    script:
      - echo defaults
""",
        monkeypatch,
    )

    assert len(specs) == 1

    s = specs[0]
    assert s.family == "defaults"
    assert s.parameters == {}
    assert s.keywords == []
    assert s.attributes["description"] == "Yaml test instance"
    assert s.command == ["/bin/sh", "-c", "set -e\necho defaults"]


def test_lock_parameter_cartesian_product_and_template_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = lock_yaml(
        tmp_path,
        "test_matrix.yaml",
        """
tests:
  matrix:
    description: "Matrix YAML test"
    script:
      - echo "${animal}-${count}-${COUNT}-${missing}"
    keywords:
      - matrix
    parameters:
      animal: [cat, dog]
      count: [1, 2]
""",
        monkeypatch,
    )

    assert len(specs) == 4

    assert [s.family for s in specs] == ["matrix", "matrix", "matrix", "matrix"]
    assert [s.parameters for s in specs] == [
        {"animal": "cat", "count": 1},
        {"animal": "cat", "count": 2},
        {"animal": "dog", "count": 1},
        {"animal": "dog", "count": 2},
    ]
    assert [s.command[2] for s in specs] == [
        'set -e\necho "cat-1-1-${missing}"',
        'set -e\necho "cat-2-2-${missing}"',
        'set -e\necho "dog-1-1-${missing}"',
        'set -e\necho "dog-2-2-${missing}"',
    ]

    for s in specs:
        assert s.keywords == ["matrix"]
        assert s.attributes["description"] == "Matrix YAML test"


def test_lock_multiple_named_tests_in_one_yaml_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = lock_yaml(
        tmp_path,
        "test_multiple.yaml",
        """
tests:
  first:
    script:
      - echo first

  second:
    script:
      - echo "${value}"
    parameters:
      value: [a, b, c]
""",
        monkeypatch,
    )

    assert len(specs) == 4

    assert [s.family for s in specs] == [
        "first",
        "second",
        "second",
        "second",
    ]
    assert [s.parameters for s in specs] == [
        {},
        {"value": "a"},
        {"value": "b"},
        {"value": "c"},
    ]
    assert [s.command[2] for s in specs] == [
        "set -e\necho first",
        'set -e\necho "a"',
        'set -e\necho "b"',
        'set -e\necho "c"',
    ]


def test_lock_preserves_yaml_parameter_value_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = lock_yaml(
        tmp_path,
        "test_types.yaml",
        """
tests:
  typed:
    script:
      - echo "${integer}-${floating}-${boolean}"
    parameters:
      integer: [1]
      floating: [2.5]
      boolean: [true]
""",
        monkeypatch,
    )

    assert len(specs) == 1
    assert specs[0].parameters == {
        "integer": 1,
        "floating": 2.5,
        "boolean": True,
    }
    assert specs[0].command[2] == 'set -e\necho "1-2.5-True"'


@pytest.mark.parametrize(
    ("text", "match"),
    [
        (
            """
not_tests:
  bad:
    script:
      - echo bad
""",
            "missing required top-level 'tests'",
        ),
        (
            """
tests: []
""",
            "'tests' must be a mapping",
        ),
        (
            """
tests:
  bad:
    script: echo bad
""",
            "tests.bad.script must be a list of strings",
        ),
        (
            """
tests:
  bad:
    script:
      - echo bad
    keywords: yaml
""",
            "tests.bad.keywords must be a list of strings",
        ),
        (
            """
tests:
  bad:
    script:
      - echo bad
    parameters:
      n: 1
""",
            "tests.bad.parameters.n must be a list",
        ),
        (
            """
tests:
  bad:
    script:
      - 123
""",
            "tests.bad.script must be a list of strings",
        ),
    ],
)
def test_lock_rejects_invalid_yaml_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    match: str,
) -> None:
    gen = make_generator(tmp_path, "test_bad.yaml", text, monkeypatch)

    with pytest.raises(ValueError, match=match):
        gen.lock()


def test_describe_includes_file_keywords_and_case_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gen = make_generator(
        tmp_path,
        "test_describe.yaml",
        """
tests:
  described:
    keywords:
      - yaml
      - smoke
    script:
      - echo described
    parameters:
      n: [1, 2]
""",
        monkeypatch,
    )

    description = gen.describe()

    assert "--- test_describe.yaml ------------" in description
    assert f"File: {tmp_path / 'test_describe.yaml'}" in description
    assert "Keywords: yaml, smoke" in description
    assert "2 test specs:" in description

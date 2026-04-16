# canary-yaml

`canary-yaml` is a simple `canary` plugin that adds support for YAML-defined tests. It is intended as an illustrative example of how to write a generator plugin: a YAML file is discovered during collection, parsed, and expanded into one or more test cases (including optional cartesian products of parameters).

## Installation

`canary-yaml` is distributed as a Python package and can be installed with `pip`.

### Install into a virtual environment (recommended)

```console
python3 -m venv venv
source venv/bin/activate
python3 -m pip install "canary_yaml @ git+ssh://git@github.com/sandialabs/canary-yaml"
```

Installing via pip registers the plugin as a canary entry point, so canary will automatically discover it.
Developer install (editable)

```console
console
python3 -m pip install --editable git+ssh://git@github.com/sandialabs/canary-yaml#egg=canary-yaml
```

This typically places the source under venv/src/ (depending on your environment). Changes will be immediately visible to Python and canary.
Alternatively:

```console
git clone git@github.com:sandialabs/canary-yaml
cd canary-yaml
python3 -m pip install --editable .
```

## Usage

Create a YAML test file named test_*.yaml (the plugin looks for files matching test_*.yaml).
Example: test_example.yaml

```yaml
tests:
  hello:
    description: "Print a message"
    keywords: ["smoke", "yaml"]
    script:
      - echo "Hello from YAML"

  parameterized:
    description: "Simple parameter sweep"
    keywords: ["yaml"]
    parameters:
      n: [1, 2, 3]
      msg: ["A", "B"]
    script:
      - echo "n=$n msg=$msg"
      - test "$n" -ge 2
      - echo "only runs when n>=2"
```

### Notes:

- script is a list of shell commands.
- The plugin runs scripts via sh -c with set -e, so the test stops at the first failing command.
- parameters expands to the cartesian product; the example above produces 6 cases: parameterized.n=1,msg=A, parameterized.n=1,msg=B, ... etc.

### Run

From the directory that contains the YAML file (or from anywhere, by pointing canary at the search path):

```console
canary run .
```

Or, explicitly pass a search root:

```console
canary run /path/to/tests
```

canary will discover test_example.yaml, generate test cases, and execute them.

### Optional: verify discovery (describe)

If your canary build includes the describe subcommand:

```console
canary describe .
```

This prints the discovered cases and their expanded parameter combinations.

## Documentation

Canary docs: https://canary-wm.readthedocs.io

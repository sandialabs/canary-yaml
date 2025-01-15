# canary-yaml

`canary` plugin demonstrating a simple `yaml` test file generator.


## Installation

`canary-yaml` is distributed as a python library and is most easily installed via `pip` (or other compatible tool):

```console
python3 -m venv venv
source venv/bin/activate
python3 -m pip install "canary_yaml @ git+ssh://git@cee-gitlab.sandia.gov/ascic-test-infra/plugins/canary-yaml"
```

Installing via `pip` will register the `canary-yaml` `canary` entry points with the python installation, thereby making them visible to `canary`.

For developers wanting to edit `canary-yaml`, install the package in editable mode:

```console
python3 -m pip install --editable git+ssh://git@cee-gitlab.sandia.gov/ascic-test-infra/plugins/canary-yaml#egg=canary-yaml
```

which will leave a copy of `canary-yaml` in `venv/src` directory (assuming you installed it into the virtual environment created above).  Edits made to the source will be immediately visible by the Python interpreter and `canary`.  Alternatively, the source can be cloned and then installed in editable mode:

```console
git clone git@cee-gitlab.sandia.gov:ascic-test-infra/plugins/canary-yaml
cd canary-yaml
python3 -m pip install --editable .
```

## Documentation

- [canary website](http://ascic-test-infra.cee-gitlab.lan/canary/)

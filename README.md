# nvtest-yaml

`nvtest` plugin demonstrating a simple `yaml` test file generator.


## Installation

`nvtest-yaml` is distributed as a python library and is most easily installed via `pip` (or other compatible tool):

```console
python3 -m venv venv
source venv/bin/activate
python3 -m pip install "nvtest_yaml @ git+ssh://git@cee-gitlab.sandia.gov/ascic-test-infra/plugins/nvtest-yaml"
```

Installing via `pip` will register the `nvtest-yaml` `nvtest` entry points with the python installation, thereby making them visible to `nvtest`.

For developers wanting to edit `nvtest-yaml`, install the package in editable mode:

```console
python3 -m pip install --editable git+ssh://git@cee-gitlab.sandia.gov/ascic-test-infra/plugins/nvtest-yaml#egg=nvtest-yaml
```

which will leave a copy of `nvtest-yaml` in `venv/src` directory (assuming you installed it into the virtual environment created above).  Edits made to the source will be immediately visible by the Python interpreter and `nvtest`.  Alternatively, the source can be cloned and then installed in editable mode:

```console
git clone git@cee-gitlab.sandia.gov:ascic-test-infra/plugins/nvtest-yaml
cd nvtest-yaml
python3 -m pip install --editable .
```

## Documentation

- [nvtest website](http://ascic-test-infra.cee-gitlab.lan/nvtest/)

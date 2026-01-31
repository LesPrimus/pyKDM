# pyKDM

Python wrapper for DCP-o-matic CLI tools (DCP creation and KDM generation).

## Requirements

- Python 3.12+
- [DCP-o-matic](https://dcpomatic.com/) installed (provides `dcpomatic2_cli` and `dcpomatic2_kdm_cli`)

## Installation

```bash
uv add pykdm
```

Or with pip:

```bash
pip install pykdm
```

## CLI Usage

### KDM Generation

Generate a KDM for an encrypted DCP:

```bash
pykdm kdm generate /path/to/dcp \
  -c /path/to/certificate.pem \
  -o /path/to/output.kdm.xml \
  -f "2024-01-01" \
  -t "2024-01-31" \
  --cinema-name "My Cinema" \
  --screen-name "Screen 1"
```

Generate a KDM from a DKDM:

```bash
pykdm kdm generate-dkdm /path/to/dkdm.xml \
  -c /path/to/certificate.pem \
  -o /path/to/output.kdm.xml \
  -f "2024-01-01" \
  -t "2024-01-31"
```

### DCP Creation

Create a DCP from a DCP-o-matic project:

```bash
pykdm dcp create /path/to/project.dcp -o /path/to/output
```

Create an encrypted DCP:

```bash
pykdm dcp create /path/to/project.dcp -o /path/to/output -e
```

### Version Info

```bash
pykdm kdm version
pykdm dcp version
```

### Options

Run `pykdm --help` or `pykdm <command> --help` for all available options.

## Python API

### KDM Generation

```python
from datetime import datetime, timedelta
from pathlib import Path
from pykdm import KDMGenerator, KDMType

generator = KDMGenerator()

result = generator.generate(
    dcp=Path("/path/to/encrypted_dcp"),
    certificate=Path("/path/to/certificate.pem"),
    output=Path("/path/to/output.kdm.xml"),
    valid_from=datetime.now(),
    valid_to=datetime.now() + timedelta(days=7),
    kdm_type=KDMType.MODIFIED_TRANSITIONAL_1,
    cinema_name="My Cinema",
    screen_name="Screen 1",
)

print(f"KDM created at: {result.output_path}")
```

### DCP Creation

```python
from pathlib import Path
from pykdm import DCPCreator

creator = DCPCreator()

result = creator.create(
    project=Path("/path/to/project.dcp"),
    output=Path("/path/to/output"),
    encrypt=True,
)

print(f"DCP created at: {result.output_path}")
```

## KDM Types

- `modified-transitional-1` (default) - Most compatible format
- `dci-any` - DCI compliant, any device
- `dci-specific` - DCI compliant, specific device

## License

MIT
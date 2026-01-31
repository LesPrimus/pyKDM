# pyKDM

Python wrapper for DCP-o-matic CLI tools (DCP creation and KDM generation).

## Requirements

- Python 3.12+
- [DCP-o-matic](https://dcpomatic.com/) installed (provides `dcpomatic2_cli`, `dcpomatic2_kdm_cli`, and `dcpomatic2_create`)

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

### DCP Project Creation (from video files)

Create a DCP-o-matic project from video/audio files:

```bash
pykdm dcp create-from-video video.mp4 -o ./my-project -n "My Film"
```

Create a project with multiple content files:

```bash
pykdm dcp create-from-video video.mp4 audio.wav -o ./project
```

Create a project and build the DCP in one step:

```bash
pykdm dcp create-from-video video.mp4 -o ./project --build
```

Create an encrypted DCP with custom output location:

```bash
pykdm dcp create-from-video video.mp4 -o ./project -e --build --dcp-output ./dcp
```

Specify content type and resolution:

```bash
pykdm dcp create-from-video video.mp4 -o ./project -c TLR --fourk --standard smpte
```

### Version Info

```bash
pykdm kdm version
pykdm dcp version
pykdm dcp project-version
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

### DCP Project Creation (from video files)

```python
from pathlib import Path
from pykdm import DCPProjectCreator, DCPContentType, ContainerRatio, DCPStandard, Resolution

creator = DCPProjectCreator()

# Create a project
result = creator.create(
    content=Path("/path/to/video.mp4"),
    output=Path("/path/to/project"),
    name="My Film",
    content_type=DCPContentType.FTR,
    container_ratio=ContainerRatio.RATIO_185,
    standard=DCPStandard.SMPTE,
    resolution=Resolution.TWO_K,
)

print(f"Project created at: {result.output_path}")
```

Create and build DCP in one step:

```python
from pathlib import Path
from pykdm import DCPProjectCreator

creator = DCPProjectCreator()

project_result, dcp_result = creator.create_and_build(
    content=[Path("/path/to/video.mp4"), Path("/path/to/audio.wav")],
    output=Path("/path/to/project"),
    dcp_output=Path("/path/to/dcp"),
    name="My Film",
    encrypt=True,
)

print(f"Project created at: {project_result.output_path}")
print(f"DCP created at: {dcp_result.output_path}")
```

## KDM Types

- `modified-transitional-1` (default) - Most compatible format
- `dci-any` - DCI compliant, any device
- `dci-specific` - DCI compliant, specific device

## DCP Content Types

- `FTR` - Feature
- `SHR` - Short
- `TLR` - Trailer
- `TST` - Test
- `XSN` - Transitional
- `RTG` - Rating
- `TSR` - Teaser
- `POL` - Policy
- `PSA` - Public Service Announcement
- `ADV` - Advertisement

## Container Ratios

- `119` - 1.19:1
- `133` - 1.33:1 (4:3)
- `137` - 1.37:1 (Academy)
- `138` - 1.38:1
- `166` - 1.66:1 (European Widescreen)
- `178` - 1.78:1 (16:9)
- `185` - 1.85:1 (Flat)
- `239` - 2.39:1 (Scope)

## DCP Standards

- `smpte` - SMPTE standard (recommended)
- `interop` - Interop standard (legacy)

## License

MIT
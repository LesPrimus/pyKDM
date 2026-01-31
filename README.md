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
pykdm kdm generate /path/to/dcpomatic-project \
  -c /path/to/certificate.pem \
  -o /path/to/output.kdm.xml \
  -f "2024-01-01" \
  -t "2024-01-31" \
  --cinema-name "My Cinema" \
  --screen-name "Screen 1"
```

Note: The path should be the DCP-o-matic project folder (containing `metadata.xml`),
not the DCP output subfolder.

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

### Test Certificate Generation

Generate a test projector certificate for KDM testing:

```bash
pykdm cert generate test_projector.pem
```

Generate with custom device info:

```bash
pykdm cert generate projector.pem -m Barco -M DP2K -s ABC123
```

Generate with different DCI role:

```bash
pykdm cert generate cert.pem --role LINK_DECRYPTOR
```

Generate a CA + leaf certificate chain:

```bash
pykdm cert generate-chain ./test-certs -m Christie -M CP4230 -s XYZ789
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

# Note: project should be the DCP-o-matic project folder (containing metadata.xml),
# not the DCP output subfolder
result = generator.generate(
    project=Path("/path/to/dcpomatic-project"),
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

### Test Certificate Generation

```python
from pathlib import Path
from pykdm import CertificateGenerator, DCIRole

generator = CertificateGenerator()

# Generate a single test certificate
result = generator.generate(
    output=Path("projector.pem"),
    manufacturer="Barco",
    model="DP2K",
    serial="ABC123",
    role=DCIRole.PROJECTOR,
    validity_days=3650,
)

print(f"Certificate: {result.certificate_path}")
print(f"Private key: {result.private_key_path}")
print(f"Thumbprint: {result.thumbprint}")
```

Generate a CA + leaf certificate chain:

```python
from pathlib import Path
from pykdm import CertificateGenerator

generator = CertificateGenerator()

ca_result, leaf_result = generator.generate_chain(
    output_dir=Path("./test-certs"),
    manufacturer="Christie",
    model="CP4230",
    serial="XYZ789",
)

print(f"CA certificate: {ca_result.certificate_path}")
print(f"Leaf certificate: {leaf_result.certificate_path}")
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

## DCI Certificate Roles

For test certificate generation:

- `PROJECTOR` - Media Decryptor (LE.SPB-MD) - default
- `LINK_DECRYPTOR` - Link Decryptor (LE.SPB-LD)
- `SECURE_PROCESSOR` - Secure Processor (LE.SPB-SP)
- `CS` - Content Signer
- `SMPTE` - SMPTE role

Note: Test certificates are self-signed and won't work with real DCI infrastructure.

## License

MIT
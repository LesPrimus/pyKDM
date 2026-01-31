from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .exceptions import CertificateGenerationError


class DCIRole(Enum):
    """DCI certificate role prefixes."""

    # Leaf entities
    PROJECTOR = "LE.SPB-MD"  # Media Decryptor (projector)
    LINK_DECRYPTOR = "LE.SPB-LD"  # Link Decryptor
    SECURE_PROCESSOR = "LE.SPB-SP"  # Secure Processor

    # Other common roles
    CS = "CS"  # Content Signer
    SMPTE = "smpte"  # SMPTE role


@dataclass
class CertificateResult:
    """Result of a certificate generation."""

    certificate_path: Path
    private_key_path: Path | None
    thumbprint: str


class CertificateGenerator:
    """Generator for test DCI-style certificates."""

    def __init__(self, key_size: int = 2048):
        """
        Initialize the certificate generator.

        Args:
            key_size: RSA key size in bits (default 2048 for DCI compatibility).
        """
        if key_size < 2048:
            raise CertificateGenerationError("Key size must be at least 2048 bits for DCI")
        self.key_size = key_size

    def generate(
        self,
        output: Path,
        manufacturer: str = "TestManufacturer",
        model: str = "TestProjector",
        serial: str = "12345",
        role: DCIRole = DCIRole.PROJECTOR,
        organization: str | None = None,
        validity_days: int = 3650,
        save_private_key: bool = True,
    ) -> CertificateResult:
        """
        Generate a test DCI-style certificate.

        Args:
            output: Output path for the certificate (.pem file).
            manufacturer: Device manufacturer name.
            model: Device model name.
            serial: Device serial number.
            role: DCI role for the certificate (default: projector).
            organization: Organization name (defaults to manufacturer).
            validity_days: Certificate validity period in days (default: 10 years).
            save_private_key: Whether to save the private key (default: True).

        Returns:
            CertificateResult with certificate path and thumbprint.

        Raises:
            CertificateGenerationError: If certificate generation fails.
        """
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
            )

            # Build DCI-style common name: role.Manufacturer.Model.Serial
            cn = f"{role.value}.{manufacturer}.{model}.{serial}"
            org = organization or manufacturer

            # Build certificate subject/issuer (self-signed)
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, model),
                x509.NameAttribute(NameOID.COMMON_NAME, cn),
                x509.NameAttribute(NameOID.DN_QUALIFIER, serial),
            ])

            now = datetime.now(timezone.utc)
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=validity_days))
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .add_extension(
                    x509.KeyUsage(
                        key_encipherment=True,
                        digital_signature=True,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        key_cert_sign=False,
                        crl_sign=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .sign(private_key, hashes.SHA256())
            )

            # Calculate thumbprint (SHA-256 fingerprint)
            thumbprint = cert.fingerprint(hashes.SHA256()).hex()

            # Ensure output directory exists
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)

            # Save certificate
            with open(output, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            # Save private key if requested
            key_path = None
            if save_private_key:
                key_path = output.with_suffix(".key.pem")
                with open(key_path, "wb") as f:
                    f.write(
                        private_key.private_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                            encryption_algorithm=serialization.NoEncryption(),
                        )
                    )

            return CertificateResult(
                certificate_path=output,
                private_key_path=key_path,
                thumbprint=thumbprint,
            )

        except Exception as e:
            raise CertificateGenerationError(f"Failed to generate certificate: {e}") from e

    def generate_chain(
        self,
        output_dir: Path,
        manufacturer: str = "TestManufacturer",
        model: str = "TestProjector",
        serial: str = "12345",
        validity_days: int = 3650,
    ) -> tuple[CertificateResult, CertificateResult]:
        """
        Generate a simple CA + leaf certificate chain for testing.

        This creates a self-signed CA certificate and a leaf certificate
        signed by that CA, mimicking a simplified DCI certificate chain.

        Args:
            output_dir: Output directory for the certificates.
            manufacturer: Device manufacturer name.
            model: Device model name.
            serial: Device serial number.
            validity_days: Certificate validity period in days.

        Returns:
            Tuple of (ca_result, leaf_result).

        Raises:
            CertificateGenerationError: If certificate generation fails.
        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate CA key and certificate
            ca_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
            )

            ca_cn = f"DC.{manufacturer}.TestCA"
            ca_subject = ca_issuer = x509.Name([
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, manufacturer),
                x509.NameAttribute(NameOID.COMMON_NAME, ca_cn),
            ])

            now = datetime.now(timezone.utc)
            ca_cert = (
                x509.CertificateBuilder()
                .subject_name(ca_subject)
                .issuer_name(ca_issuer)
                .public_key(ca_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=validity_days))
                .add_extension(
                    x509.BasicConstraints(ca=True, path_length=1),
                    critical=True,
                )
                .add_extension(
                    x509.KeyUsage(
                        key_encipherment=False,
                        digital_signature=True,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        key_cert_sign=True,
                        crl_sign=True,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .sign(ca_key, hashes.SHA256())
            )

            ca_path = output_dir / "ca.pem"
            ca_key_path = output_dir / "ca.key.pem"

            with open(ca_path, "wb") as f:
                f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            with open(ca_key_path, "wb") as f:
                f.write(
                    ca_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            ca_result = CertificateResult(
                certificate_path=ca_path,
                private_key_path=ca_key_path,
                thumbprint=ca_cert.fingerprint(hashes.SHA256()).hex(),
            )

            # Generate leaf key and certificate (signed by CA)
            leaf_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
            )

            leaf_cn = f"{DCIRole.PROJECTOR.value}.{manufacturer}.{model}.{serial}"
            leaf_subject = x509.Name([
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, manufacturer),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, model),
                x509.NameAttribute(NameOID.COMMON_NAME, leaf_cn),
                x509.NameAttribute(NameOID.DN_QUALIFIER, serial),
            ])

            leaf_cert = (
                x509.CertificateBuilder()
                .subject_name(leaf_subject)
                .issuer_name(ca_subject)  # Issued by CA
                .public_key(leaf_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=validity_days))
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .add_extension(
                    x509.KeyUsage(
                        key_encipherment=True,
                        digital_signature=True,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        key_cert_sign=False,
                        crl_sign=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .sign(ca_key, hashes.SHA256())  # Signed by CA key
            )

            leaf_path = output_dir / "leaf.pem"
            leaf_key_path = output_dir / "leaf.key.pem"

            with open(leaf_path, "wb") as f:
                f.write(leaf_cert.public_bytes(serialization.Encoding.PEM))
            with open(leaf_key_path, "wb") as f:
                f.write(
                    leaf_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            leaf_result = CertificateResult(
                certificate_path=leaf_path,
                private_key_path=leaf_key_path,
                thumbprint=leaf_cert.fingerprint(hashes.SHA256()).hex(),
            )

            return ca_result, leaf_result

        except Exception as e:
            raise CertificateGenerationError(f"Failed to generate certificate chain: {e}") from e
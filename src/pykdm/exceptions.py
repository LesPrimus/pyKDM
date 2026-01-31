class PyKDMError(Exception):
    """Base exception for pyKDM."""

    pass


class DCPCreationError(PyKDMError):
    """Raised when DCP creation fails."""

    pass


class KDMGenerationError(PyKDMError):
    """Raised when KDM generation fails."""

    pass


class DCPProjectCreationError(PyKDMError):
    """Raised when DCP project creation fails."""

    pass


class CertificateGenerationError(PyKDMError):
    """Raised when certificate generation fails."""

    pass
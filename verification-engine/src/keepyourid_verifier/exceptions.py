
class CredentialVerificationError(Exception):
    """Base exception for credential verification."""


class InvalidCredentialError(CredentialVerificationError):
    pass


class InvalidProofError(CredentialVerificationError):
    pass

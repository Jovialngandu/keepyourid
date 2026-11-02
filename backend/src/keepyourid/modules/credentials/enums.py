
from enum import Enum


class CredentialStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"

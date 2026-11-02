
from enum import Enum


class DIDStatus(str, Enum):
    REGISTERED = "REGISTERED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"

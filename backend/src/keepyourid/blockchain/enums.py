from enum import Enum


class BlockchainTransactionStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class BlockchainOperation(str, Enum):
    REGISTER_ISSUER = "REGISTER_ISSUER"
    UPDATE_STATUS = "UPDATE_STATUS"
    UPDATE_METADATA = "UPDATE_METADATA"
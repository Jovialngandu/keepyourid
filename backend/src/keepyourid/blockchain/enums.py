from enum import StrEnum


class BlockchainTransactionStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class BlockchainOperation(StrEnum):
    REGISTER_ISSUER = "REGISTER_ISSUER"
    UPDATE_STATUS = "UPDATE_STATUS"
    UPDATE_METADATA = "UPDATE_METADATA"
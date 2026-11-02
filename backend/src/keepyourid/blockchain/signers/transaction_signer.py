from typing import Protocol


class TransactionSigner(Protocol):
    @property
    def address(self) -> str:
        ...

    def sign_transaction(self, transaction: dict) -> bytes:
        ...
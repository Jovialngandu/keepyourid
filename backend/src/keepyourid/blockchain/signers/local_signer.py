from eth_account import Account

from keepyourid.blockchain.signers.transaction_signer import (
    TransactionSigner,
)


class LocalAccountSigner:
    def __init__(self, private_key: str) -> None:
        if not private_key:
            raise ValueError("Private key cannot be empty")

        self._account = Account.from_key(private_key)

    @property
    def address(self) -> str:
        return self._account.address

    def sign_transaction(self, transaction: dict) -> bytes:
        signed = self._account.sign_transaction(transaction)
        return signed.raw_transaction
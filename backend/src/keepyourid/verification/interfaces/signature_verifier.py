from typing import Protocol


class SignatureVerifier(Protocol):
    def recover_signer(
        self,
        message: str,
        signature: str,
    ) -> str:
        ...
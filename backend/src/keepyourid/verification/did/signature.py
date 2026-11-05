from eth_account import Account
from eth_account.messages import encode_defunct

from keepyourid.verification.interfaces.signature_verifier import (
    SignatureVerifier,
)


class SignatureVerificationError(Exception):
    pass


def build_authentication_message(
    did: str,
    challenge: str,
    purpose: str,
    domain: str,
    issued_at: str,
    expires_at: str,
) -> str:
    return (
        "KeepYourID DID Authentication\n"
        f"DID: {did}\n"
        f"Challenge: {challenge}\n"
        f"Purpose: {purpose}\n"
        f"Domain: {domain}\n"
        f"Issued At: {issued_at}\n"
        f"Expires At: {expires_at}"
    )


class EthereumSignatureVerifier(SignatureVerifier):

    def recover_signer(
        self,
        message: str,
        signature: str,
    ) -> str:
        try:
            signable_message = encode_defunct(text=message)

            return Account.recover_message(
                signable_message,
                signature=signature,
            )

        except Exception as exc:
            raise SignatureVerificationError(
                "Unable to recover signer from signature."
            ) from exc

import base64
import json

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import is_address, to_checksum_address


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def build_signing_input(
    credential: dict,
    verification_method: str,
) -> str:
    header = {
        "alg": "ES256K",
        "cty": "vc",
        "kid": verification_method,
        "typ": "vc+jwt",
    }

    encoded_header = _base64url_encode(
        json.dumps(
            header,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )

    encoded_payload = _base64url_encode(
        json.dumps(
            credential,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )

    return f"{encoded_header}.{encoded_payload}"


def verify_signature(
    credential: dict,
    proof: dict,
) -> tuple[bool, str | None]:
    signature = proof.get("signature")
    verification_method = proof.get("verificationMethod")
    expected_signer = proof.get("signer")

    if not all([signature, verification_method, expected_signer]):
        return False, None

    if not is_address(expected_signer):
        return False, None

    if not verification_method.endswith("#controller"):
        return False, None

    signing_input = build_signing_input(
        credential,
        verification_method,
    )

    try:
        message = encode_defunct(text=signing_input)

        recovered_address = Account.recover_message(
            message,
            signature=signature,
        )

        valid = (
            to_checksum_address(recovered_address)
            == to_checksum_address(expected_signer)
        )

        return valid, recovered_address

    except Exception:
        return False, None

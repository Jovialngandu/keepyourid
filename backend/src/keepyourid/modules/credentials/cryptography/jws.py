
import base64
import hashlib
import json

from eth_keys import keys
from eth_keys.datatypes import Signature


class JWSVerificationError(Exception):
    pass


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def build_signing_input(
    credential: dict,
    key_id: str,
) -> str:
    """
    Builds the JWS signing input.

    The private key never enters the backend.
    The issuer signs this input using ES256K.
    """

    header = {
        "alg": "ES256K",
        "typ": "vc+jwt",
        "kid": key_id,
    }

    header_bytes = json.dumps(
        header,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    payload_bytes = json.dumps(
        credential,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")

    encoded_header = b64url_encode(header_bytes)
    encoded_payload = b64url_encode(payload_bytes)

    return f"{encoded_header}.{encoded_payload}"


def complete_jws(
    signing_input: str,
    signature: str,
) -> str:
    """
    Completes a compact JWS using the issuer's signature.
    """

    signature_bytes = b64url_decode(signature)

    if len(signature_bytes) != 64:
        raise JWSVerificationError(
            "ES256K signature must contain exactly 64 bytes."
        )

    return f"{signing_input}.{b64url_encode(signature_bytes)}"


def load_public_key(public_key_hex: str) -> keys.PublicKey:
    """
    Loads an uncompressed secp256k1 public key.

    Accepted formats:
    - 0x + 128 hex characters (X || Y)
    - 0x04 + 130 hex characters (04 || X || Y)
    """

    raw = public_key_hex.removeprefix("0x")

    if len(raw) == 130 and raw.startswith("04"):
        raw = raw[2:]

    if len(raw) != 128:
        raise JWSVerificationError(
            "Invalid secp256k1 public key format."
        )

    try:
        return keys.PublicKey(bytes.fromhex(raw))
    except (ValueError, Exception) as exc:
        raise JWSVerificationError(
            "Unable to load issuer public key."
        ) from exc


def verify_jws(
    token: str,
    public_key_hex: str,
    expected_key_id: str,
) -> dict:
    """
    Verifies a VC-JWT signed with ES256K.

    Returns the verified VC document.
    """

    parts = token.split(".")

    if len(parts) != 3:
        raise JWSVerificationError("Invalid compact JWS format.")

    encoded_header, encoded_payload, encoded_signature = parts

    try:
        header = json.loads(b64url_decode(encoded_header))
        payload = json.loads(b64url_decode(encoded_payload))
        signature_bytes = b64url_decode(encoded_signature)
    except (ValueError, UnicodeDecodeError) as exc:
        raise JWSVerificationError(
            "Invalid JWS encoding."
        ) from exc

    if header.get("alg") != "ES256K":
        raise JWSVerificationError("Unsupported signing algorithm.")

    if header.get("typ") != "vc+jwt":
        raise JWSVerificationError("Invalid credential media type.")

    if header.get("kid") != expected_key_id:
        raise JWSVerificationError("Unexpected issuer key identifier.")

    if not isinstance(payload, dict):
        raise JWSVerificationError("Invalid credential payload.")

    if len(signature_bytes) != 64:
        raise JWSVerificationError("Invalid signature length.")

    signing_input = f"{encoded_header}.{encoded_payload}"
    digest = hashlib.sha256(signing_input.encode("ascii")).digest()

    try:
        public_key = load_public_key(public_key_hex)
        signature = Signature(signature_bytes)

        valid = public_key.verify_msg_hash(digest, signature)
    except Exception as exc:
        raise JWSVerificationError(
            "Cryptographic verification failed."
        ) from exc

    if not valid:
        raise JWSVerificationError("Invalid credential signature.")

    return payload

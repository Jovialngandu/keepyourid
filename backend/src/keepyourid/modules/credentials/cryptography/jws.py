import base64
import binascii
import hashlib
import json
import re

from eth_keys import keys
from eth_keys.datatypes import Signature


ALGORITHM = "ES256K"
CREDENTIAL_TYPE = "vc+jwt"
CONTENT_TYPE = "vc"
SIGNATURE_LENGTH = 64


class JWSVerificationError(Exception):
    """Raised when a JWS cannot be constructed or verified."""


def b64url_encode(value: bytes) -> str:
    """Encodes bytes using unpadded Base64URL."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    """Strictly decodes an unpadded Base64URL value."""

    if not isinstance(value, str) or not value:
        raise JWSVerificationError("Invalid Base64URL value.")

    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise JWSVerificationError("Invalid Base64URL characters.")

    if len(value) % 4 == 1:
        raise JWSVerificationError("Invalid Base64URL length.")

    try:
        padding = "=" * (-len(value) % 4)

        decoded = base64.b64decode(
            value + padding,
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise JWSVerificationError(
            "Invalid Base64URL encoding."
        ) from exc

    if b64url_encode(decoded) != value:
        raise JWSVerificationError(
            "Non-canonical Base64URL encoding."
        )

    return decoded


def _json_bytes(value: dict) -> bytes:
    """Serializes a JSON object deterministically."""

    try:
        return json.dumps(
            value,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise JWSVerificationError(
            "Unable to serialize JSON value."
        ) from exc


def build_signing_input(
    credential: dict,
    key_id: str,
) -> str:
    """
    Builds the compact JWS signing input.

    The external issuer signs the ASCII bytes of the returned value.
    The backend never receives or stores the private key.
    """

    if not isinstance(credential, dict):
        raise JWSVerificationError(
            "Credential must be a JSON object."
        )

    if not isinstance(key_id, str) or not key_id.strip():
        raise JWSVerificationError(
            "A valid issuer key identifier is required."
        )

    header = {
        "alg": ALGORITHM,
        "typ": CREDENTIAL_TYPE,
        "cty": CONTENT_TYPE,
        "kid": key_id,
    }

    encoded_header = b64url_encode(_json_bytes(header))
    encoded_payload = b64url_encode(_json_bytes(credential))

    return f"{encoded_header}.{encoded_payload}"


def complete_jws(
    signing_input: str,
    signature: str,
) -> str:
    """
    Completes a compact JWS using an external signature.

    Expected signature:
        Base64URL-encoded 64-byte ECDSA signature (r || s).

    The signer must use:
        ES256K = ECDSA secp256k1 + SHA-256.
    """

    if not isinstance(signing_input, str):
        raise JWSVerificationError(
            "Invalid JWS signing input."
        )

    parts = signing_input.split(".")

    if len(parts) != 2 or not all(parts):
        raise JWSVerificationError(
            "Invalid JWS signing input format."
        )

    signature_bytes = b64url_decode(signature)

    if len(signature_bytes) != SIGNATURE_LENGTH:
        raise JWSVerificationError("Invalid signature length.")

    return (
        f"{signing_input}."
        f"{b64url_encode(signature_bytes)}"
    )


def load_public_key(public_key_hex: str) -> keys.PublicKey:
    """
    Loads an uncompressed secp256k1 public key.

    Accepted formats:
    - 0x + 128 hexadecimal characters (X || Y)
    - 0x04 + 130 hexadecimal characters (04 || X || Y)
    """

    if not isinstance(public_key_hex, str):
        raise JWSVerificationError(
            "Invalid issuer public key."
        )

    raw = public_key_hex.removeprefix("0x")

    if len(raw) == 130 and raw.startswith("04"):
        raw = raw[2:]

    if not re.fullmatch(r"[0-9a-fA-F]{128}", raw):
        raise JWSVerificationError(
            "Invalid secp256k1 public key format."
        )

    try:
        return keys.PublicKey(bytes.fromhex(raw))
    except (ValueError, TypeError) as exc:
        raise JWSVerificationError(
            "Unable to load issuer public key."
        ) from exc


def verify_jws(
    token: str,
    public_key_hex: str,
    expected_key_id: str,
) -> dict:
    if not isinstance(token, str):
        raise JWSVerificationError("Invalid compact JWS format.")

    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise JWSVerificationError("Invalid compact JWS format.")

    encoded_header, encoded_payload, encoded_signature = parts

    try:
        header = json.loads(
            b64url_decode(encoded_header).decode("utf-8")
        )
        credential_payload = json.loads(
            b64url_decode(encoded_payload).decode("utf-8")
        )
        signature_bytes = b64url_decode(encoded_signature)

    except (
        ValueError,
        UnicodeDecodeError,
        binascii.Error,
        JWSVerificationError,
    ) as exc:
        raise JWSVerificationError("Invalid JWS encoding.") from exc

    if not isinstance(header, dict):
        raise JWSVerificationError("Invalid JWS header.")

    if not isinstance(credential_payload, dict):
        raise JWSVerificationError("Invalid credential payload.")

    if header.get("alg") != ALGORITHM:
        raise JWSVerificationError("Unsupported signing algorithm.")

    if header.get("typ") != CREDENTIAL_TYPE:
        raise JWSVerificationError("Invalid credential media type.")

    if header.get("cty") != CONTENT_TYPE:
        raise JWSVerificationError("Invalid credential content type.")

    if header.get("kid") != expected_key_id:
        raise JWSVerificationError("Unexpected issuer key identifier.")

    if len(signature_bytes) != SIGNATURE_LENGTH:
        raise JWSVerificationError("Invalid signature length.")

    signing_input = f"{encoded_header}.{encoded_payload}"
    digest = hashlib.sha256(signing_input.encode("ascii")).digest()

    try:
        public_key = load_public_key(public_key_hex)

        r = int.from_bytes(signature_bytes[:32], "big")
        s = int.from_bytes(signature_bytes[32:], "big")

        signature_obj = Signature(vrs=(0, r, s))

        is_valid = public_key.verify_msg_hash(
            digest,
            signature_obj,
        )

    except JWSVerificationError:
        raise
    except Exception as exc:
        raise JWSVerificationError(
            "Cryptographic verification failed."
        ) from exc

    if not is_valid:
        raise JWSVerificationError("Invalid credential signature.")

    return credential_payload
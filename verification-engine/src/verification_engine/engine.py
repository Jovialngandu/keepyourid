from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any

from keepyourid.modules.credentials.cryptography.jws import JWSVerificationError, verify_jws
from keepyourid.verification.did.did_ethr import DIDEthrVerifier
from keepyourid.verification.interfaces import ResolvedDID
from keepyourid.verification.did.resolver import UniversalResolver


@dataclass
class VerificationDecision:
    valid: bool
    status: str
    issuer: str | None = None
    verification_method: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class VerificationEngineError(Exception):
    pass


def _coerce_token(credential: str | dict[str, Any]) -> str:
    if isinstance(credential, str):
        return credential

    if isinstance(credential, dict):
        if "signed_credential" in credential:
            value = credential["signed_credential"]
            if isinstance(value, str):
                return value
        if "credential" in credential:
            value = credential["credential"]
            if isinstance(value, str):
                return value

    raise VerificationEngineError("Credential input must be a JWS string or include a signed_credential field.")


def _resolve_verification_method(document: dict[str, Any], key_id: str, issuer: str) -> dict[str, Any]:
    verification_methods = document.get("verificationMethod", [])
    if not isinstance(verification_methods, list):
        raise VerificationEngineError("Issuer DID document does not expose verification methods.")

    method = next(
        (
            item
            for item in verification_methods
            if isinstance(item, dict) and item.get("id") == key_id
        ),
        None,
    )

    if method is None:
        raise VerificationEngineError("Issuer key id was not found in the DID document.")

    if method.get("controller") != issuer:
        raise VerificationEngineError("Verification method controller does not match the issuer DID.")

    return method


def _extract_public_key(method: dict[str, Any]) -> str:
    public_key_hex = method.get("publicKeyHex")
    if isinstance(public_key_hex, str) and public_key_hex:
        return public_key_hex

    jwk = method.get("publicKeyJwk")
    if not isinstance(jwk, dict):
        raise VerificationEngineError("Issuer key is missing a usable public key.")

    if jwk.get("kty") != "EC" or jwk.get("crv") != "secp256k1":
        raise VerificationEngineError("Issuer public key is not a supported secp256k1 key.")

    x = jwk.get("x")
    y = jwk.get("y")
    if not isinstance(x, str) or not isinstance(y, str):
        raise VerificationEngineError("Issuer public key JWK is incomplete.")

    import base64

    try:
        x_bytes = base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))
        y_bytes = base64.urlsafe_b64decode(y + "=" * (-len(y) % 4))
    except (ValueError, TypeError) as exc:
        raise VerificationEngineError("Issuer public key JWK is invalid.") from exc

    if len(x_bytes) != 32 or len(y_bytes) != 32:
        raise VerificationEngineError("Issuer public key JWK is incomplete.")

    return "0x" + (x_bytes + y_bytes).hex()


def verify_credential(
    credential: str | dict[str, Any],
    resolver: Any | None = None,
    resolver_url: str | None = None,
) -> VerificationDecision:
    try:
        token = _coerce_token(credential)
        parts = token.split(".")
        if len(parts) != 3 or not all(parts):
            raise VerificationEngineError("Invalid compact JWS format.")

        header_b64, payload_b64, _ = parts
        header = json.loads(__import__("base64").urlsafe_b64decode(header_b64 + "=" * (-len(header_b64) % 4)).decode("utf-8"))
        payload = json.loads(__import__("base64").urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode("utf-8"))

        if not isinstance(header, dict) or not isinstance(payload, dict):
            raise VerificationEngineError("Credential payload is not valid JSON.")

        issuer = payload.get("issuer")
        if not isinstance(issuer, str) or not issuer.startswith("did:"):
            raise VerificationEngineError("Credential issuer is missing or invalid.")

        key_id = header.get("kid")
        if not isinstance(key_id, str) or not key_id.startswith(f"{issuer}#"):
            raise VerificationEngineError("Credential key identifier is missing or mismatched with the issuer DID.")

        did_resolver = resolver or UniversalResolver(
            resolver_url or os.getenv("DID_RESOLVER_URL", "https://dev.uniresolver.io"),
            timeout=10.0,
        )
        resolved = did_resolver.resolve(issuer)
        if not isinstance(resolved, ResolvedDID):
            raise VerificationEngineError("DID resolution returned an unexpected value.")

        document = dict(resolved.document)
        if "authentication" not in document and "assertionMethod" in document:
            document["authentication"] = document["assertionMethod"]

        DIDEthrVerifier().validate_did_document(issuer, document)
        method = _resolve_verification_method(document, key_id, issuer)
        public_key_hex = _extract_public_key(method)

        verified_payload = verify_jws(token, public_key_hex, key_id)

        if verified_payload != payload:
            raise VerificationEngineError("Modified credential payload does not match the signed content.")

        if payload.get("issuer") != issuer:
            raise VerificationEngineError("Credential issuer does not match the DID in the signature.")

        return VerificationDecision(
            valid=True,
            status="valid",
            issuer=issuer,
            verification_method=key_id,
            error=None,
        )

    except (VerificationEngineError, JWSVerificationError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return VerificationDecision(
            valid=False,
            status="invalid",
            issuer=(credential.get("issuer") if isinstance(credential, dict) else None),
            verification_method=None,
            error=str(exc),
        )

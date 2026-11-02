
from uuid import UUID

from sqlalchemy.orm import Session

from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.dids.models import DID


class IssuerKeyError(Exception):
    pass


class IssuerKeyResolver:
    """
    Resolves an issuer's authorized assertion key from its stored DID Document.

    Supported public key representations:
    - publicKeyHex
    - publicKeyJwk using secp256k1
    """

    def __init__(self, session: Session):
        self.session = session

    def resolve(self, credential: VerifiableCredential) -> tuple[str, str]:
        did = self.session.get(DID, credential.issuer_did_id)

        if did is None:
            raise IssuerKeyError("Issuer DID not found.")

        if not isinstance(did.document, dict):
            raise IssuerKeyError("Issuer DID Document is invalid.")

        document = did.document
        verification_methods = document.get("verificationMethod", [])
        assertion_methods = document.get("assertionMethod", [])

        if not isinstance(verification_methods, list):
            raise IssuerKeyError("Invalid verificationMethod section.")

        if not isinstance(assertion_methods, list):
            raise IssuerKeyError("Invalid assertionMethod section.")

        methods_by_id = {
            method["id"]: method
            for method in verification_methods
            if isinstance(method, dict) and isinstance(method.get("id"), str)
        }

        # Only keys explicitly authorized for assertion are accepted.
        for assertion in assertion_methods:
            if isinstance(assertion, dict):
                method = assertion
            elif isinstance(assertion, str):
                method = methods_by_id.get(assertion)
            else:
                continue

            if not isinstance(method, dict):
                continue

            key_id = method.get("id")
            controller = method.get("controller")

            if not isinstance(key_id, str) or not key_id.startswith(
                f"{did.identifier}#"
            ):
                continue

            if controller != did.identifier:
                continue

            public_key = self._extract_public_key(method)

            if public_key:
                return key_id, public_key

        raise IssuerKeyError(
            "No supported assertion key was found in the issuer DID Document."
        )

    @staticmethod
    def _extract_public_key(method: dict) -> str | None:
        public_key_hex = method.get("publicKeyHex")

        if isinstance(public_key_hex, str):
            return public_key_hex

        jwk = method.get("publicKeyJwk")

        if not isinstance(jwk, dict):
            return None

        if jwk.get("kty") != "EC" or jwk.get("crv") != "secp256k1":
            return None

        x = jwk.get("x")
        y = jwk.get("y")

        if not isinstance(x, str) or not isinstance(y, str):
            return None

        import base64

        try:
            x_bytes = base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))
            y_bytes = base64.urlsafe_b64decode(y + "=" * (-len(y) % 4))
        except (ValueError, TypeError):
            return None

        if len(x_bytes) != 32 or len(y_bytes) != 32:
            return None

        return "0x" + (x_bytes + y_bytes).hex()


import re
from uuid import UUID

from sqlalchemy.orm import Session

from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.dids.models import DID


class IssuerKeyError(Exception):
    pass


class IssuerKeyResolver:
    """
    Resolves an issuer's authorized Ethereum assertion method.
    """

    def __init__(self, session: Session):
        self.session = session

    def resolve(self, credential: VerifiableCredential) -> tuple[str, str]:
        did = self.session.get(DID, credential.issuer_did_id)

        if did is None:
            raise IssuerKeyError("Issuer DID not found.")

        document = did.document

        if not isinstance(document, dict):
            raise IssuerKeyError("Issuer DID Document is invalid.")

        verification_methods = document.get("verificationMethod", [])
        assertion_methods = document.get("assertionMethod", [])

        if not isinstance(verification_methods, list):
            raise IssuerKeyError("Invalid verificationMethod section.")

        if not isinstance(assertion_methods, list):
            raise IssuerKeyError("Invalid assertionMethod section.")

        methods_by_id = {
            method["id"]: method
            for method in verification_methods
            if isinstance(method, dict)
            and isinstance(method.get("id"), str)
        }

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

            if not isinstance(key_id, str):
                continue

            if not key_id.startswith(f"{did.identifier}#"):
                continue

            if controller != did.identifier:
                continue

            account_id = method.get("blockchainAccountId")

            if not isinstance(account_id, str):
                continue

            match = re.fullmatch(
                r"eip155:(\d+):(0x[a-fA-F0-9]{40})",
                account_id,
            )

            if not match:
                continue

            return key_id, match.group(2)

        raise IssuerKeyError(
            "No supported Ethereum assertion method was found."
        )

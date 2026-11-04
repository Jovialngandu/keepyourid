
import re

from keepyourid.verification.interfaces import (
    DIDMethodVerifier,
)


class DIDDocumentValidationError(Exception):
    pass


class DIDEthrVerifier(DIDMethodVerifier):
    EXPECTED_CHAIN_ID = "11155111"

    DID_PATTERN = re.compile(
        r"^did:ethr:sepolia:(0x[a-fA-F0-9]{40})$"
    )

    def validate_did_document(
        self,
        did: str,
        document: dict,
    ) -> None:
        if not self.DID_PATTERN.fullmatch(did):
            raise DIDDocumentValidationError(
                "Unsupported DID. Expected did:ethr:sepolia."
            )

        if document.get("id") != did:
            raise DIDDocumentValidationError(
                "DID Document identifier does not match the requested DID."
            )

        methods = document.get("verificationMethod")

        if not isinstance(methods, list):
            raise DIDDocumentValidationError(
                "DID Document has no verification methods."
            )

        authentication = document.get("authentication")

        if not isinstance(authentication, list) or not authentication:
            raise DIDDocumentValidationError(
                "DID Document has no authentication methods."
            )

    def get_authorized_method(
        self,
        did: str,
        document: dict,
        verification_method: str,
    ) -> tuple[str, str]:
        methods = document.get("verificationMethod", [])
        authentication = document.get("authentication", [])

        authorized_ids = set()

        for entry in authentication:
            if isinstance(entry, str):
                authorized_ids.add(entry)
            elif isinstance(entry, dict) and isinstance(entry.get("id"), str):
                authorized_ids.add(entry["id"])

        method = next(
            (
                item
                for item in methods
                if isinstance(item, dict)
                and item.get("id") == verification_method
            ),
            None,
        )

        if method is None or verification_method not in authorized_ids:
            raise DIDDocumentValidationError(
                "Verification method is not authorized for authentication."
            )

        if method.get("controller") != did:
            raise DIDDocumentValidationError(
                "Verification method has an invalid controller."
            )

        account_id = method.get("blockchainAccountId")

        if not isinstance(account_id, str):
            raise DIDDocumentValidationError(
                "Missing blockchainAccountId."
            )

        parts = account_id.split(":")

        if len(parts) != 3:
            raise DIDDocumentValidationError(
                "Invalid blockchainAccountId format."
            )

        namespace, chain_id, address = parts

        if namespace != "eip155" or chain_id != self.EXPECTED_CHAIN_ID:
            raise DIDDocumentValidationError(
                "Verification method belongs to an unsupported network."
            )

        if not re.fullmatch(r"0x[a-fA-F0-9]{40}", address):
            raise DIDDocumentValidationError(
                "Invalid Ethereum address in verification method."
            )

        return verification_method, address

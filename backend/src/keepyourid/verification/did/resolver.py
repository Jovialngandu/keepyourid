from urllib.parse import quote

import httpx

from keepyourid.verification.interfaces.did_resolver import DIDResolver
from keepyourid.verification.results import ResolvedDID


class DIDResolutionError(Exception):
    pass


class UniversalResolver(DIDResolver):

    def __init__(
        self,
        endpoint: str,
        timeout: float = 10.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def resolve(self, did: str) -> ResolvedDID:

        if not isinstance(did, str) or not did.startswith("did:"):
            raise DIDResolutionError("Invalid DID format.")

        url = (
            f"{self.endpoint}/1.0/identifiers/"
            f"{quote(did, safe=':')}"
        )

        try:
            response = httpx.get(
                url,
                timeout=self.timeout,
                headers={"Accept": "application/ld+json"},
            )
            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise DIDResolutionError(
                "Unable to resolve DID."
            ) from exc

        try:
            payload = response.json()

        except ValueError as exc:
            raise DIDResolutionError(
                "Invalid resolver response."
            ) from exc

        if not isinstance(payload, dict):
            raise DIDResolutionError(
                "Invalid resolver response structure."
            )

        resolution_metadata = payload.get(
            "didResolutionMetadata",
            {},
        )

        if not isinstance(resolution_metadata, dict):
            raise DIDResolutionError(
                "Invalid DID resolution metadata."
            )

        resolution_error = resolution_metadata.get("error")

        if resolution_error:
            raise DIDResolutionError(
                f"DID resolution failed: {resolution_error}"
            )

        document = payload.get("didDocument")

        if not isinstance(document, dict):
            raise DIDResolutionError(
                "Resolver returned no valid DID Document."
            )

        document_metadata = payload.get(
            "didDocumentMetadata",
            {},
        )

        if not isinstance(document_metadata, dict):
            raise DIDResolutionError(
                "Invalid DID document metadata."
            )

        return ResolvedDID(
            did=did,
            document=document,
            metadata=document_metadata,
        )
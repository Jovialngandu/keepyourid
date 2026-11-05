
import re

from eth_utils import is_address, to_checksum_address


def extract_issuer_address(issuer_did: str) -> str | None:
    match = re.fullmatch(
        r"did:ethr(?::[^:]+)?:"
        r"(0x[a-fA-F0-9]{40})",
        issuer_did,
    )

    if not match:
        return None

    address = match.group(1)

    if not is_address(address):
        return None

    return to_checksum_address(address)


def verify_issuer(
    issuer_did: str,
    recovered_address: str | None,
) -> bool:
    if not recovered_address:
        return False

    issuer_address = extract_issuer_address(issuer_did)

    if not issuer_address:
        return False

    return (
        issuer_address
        == to_checksum_address(recovered_address)
    )

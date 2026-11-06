from web3 import Web3


ISSUER_REGISTRY_ABI = [
    {
        "inputs": [{"name": "didHash", "type": "bytes32"}],
        "name": "isRegistered",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "didHash", "type": "bytes32"}],
        "name": "isActive",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def verify_issuer_trust(
    issuer_did: str,
    rpc_url: str,
    registry_address: str,
    expected_chain_id: int = 11155111,
) -> tuple[bool | None, str | None]:
    """Return (True, None) on success, (False, msg) on definitive failure,
    and (None, msg) when trust cannot be determined (UNKNOWN)."""

    if not all([issuer_did, rpc_url, registry_address]):
        return None, "Issuer registry configuration is missing."

    if not Web3.is_address(registry_address):
        return None, "Invalid IssuerRegistry address."

    try:
        web3 = Web3(
            Web3.HTTPProvider(
                rpc_url,
                request_kwargs={"timeout": 5},
            )
        )

        if not web3.is_connected():
            return None, "Issuer registry is currently unavailable."

        if web3.eth.chain_id != expected_chain_id:
            return None, "Unexpected blockchain network."

        contract = web3.eth.contract(
            address=Web3.to_checksum_address(registry_address),
            abi=ISSUER_REGISTRY_ABI,
        )

        did_hash = Web3.keccak(text=issuer_did)

        registered = contract.functions.isRegistered(did_hash).call()

        if not registered:
            return False, "Issuer is not registered."

        active = contract.functions.isActive(did_hash).call()

        if not active:
            return False, "Issuer is not active."

        return True, None

    except Exception as exc:
        return None, f"Issuer trust verification failed: {exc}"

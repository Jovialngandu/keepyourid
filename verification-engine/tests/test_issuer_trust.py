from keepyourid_verifier.checks import issuer_trust as issuer_trust_module
from keepyourid_verifier.checks.issuer_trust import verify_issuer_trust
from keepyourid_verifier.engine import CredentialVerifier
import keepyourid_verifier.engine as engine_module


ISSUER_DID = "did:ethr:sepolia:0x1111111111111111111111111111111111111111"
RPC_URL = "https://rpc.example.com"
REGISTRY_ADDRESS = "0x2222222222222222222222222222222222222222"


class _FakeFunction:
    def __init__(self, result):
        self._result = result

    def call(self):
        return self._result


class _FakeFunctions:
    def __init__(self, registered, active):
        self._registered = registered
        self._active = active

    def isRegistered(self, did_hash):
        return _FakeFunction(self._registered)

    def isActive(self, did_hash):
        return _FakeFunction(self._active)


class _FakeContract:
    def __init__(self, registered, active):
        self.functions = _FakeFunctions(registered, active)


class _FakeEth:
    @property
    def chain_id(self):
        return FakeWeb3.chain_id

    def contract(self, address, abi):
        return _FakeContract(FakeWeb3.registered, FakeWeb3.active)


class FakeWeb3:
    """Configurable stand-in for web3.Web3."""

    connected = True
    chain_id = 11155111
    registered = True
    active = True
    init_error = None

    def __init__(self, provider=None):
        if FakeWeb3.init_error is not None:
            raise FakeWeb3.init_error
        self.eth = _FakeEth()

    def is_connected(self):
        return FakeWeb3.connected

    @staticmethod
    def is_address(value):
        return (
            isinstance(value, str)
            and value.startswith("0x")
            and len(value) == 42
        )

    @staticmethod
    def to_checksum_address(value):
        return value

    @staticmethod
    def keccak(text=None):
        return b"\x00" * 32

    class HTTPProvider:
        def __init__(self, url, request_kwargs=None):
            self.url = url


def _install_fake_web3(monkeypatch, *, connected=True, chain_id=11155111,
                       registered=True, active=True, init_error=None):
    FakeWeb3.connected = connected
    FakeWeb3.chain_id = chain_id
    FakeWeb3.registered = registered
    FakeWeb3.active = active
    FakeWeb3.init_error = init_error
    monkeypatch.setattr(issuer_trust_module, "Web3", FakeWeb3)


def test_missing_configuration_returns_unknown():
    result, message = verify_issuer_trust(
        issuer_did="",
        rpc_url="",
        registry_address="",
    )

    assert result is None
    assert message == "Issuer registry configuration is missing."


def test_missing_rpc_url_returns_unknown():
    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url="",
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is None
    assert message == "Issuer registry configuration is missing."


def test_invalid_registry_address_returns_unknown():
    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address="not-an-address",
    )

    assert result is None
    assert message == "Invalid IssuerRegistry address."


def test_registry_unreachable_returns_unknown(monkeypatch):
    _install_fake_web3(monkeypatch, connected=False)

    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is None
    assert message == "Issuer registry is currently unavailable."


def test_rpc_failure_returns_unknown(monkeypatch):
    _install_fake_web3(monkeypatch, init_error=ConnectionError("RPC timeout"))

    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is None
    assert "Issuer trust verification failed" in message


def test_unexpected_chain_returns_unknown(monkeypatch):
    _install_fake_web3(monkeypatch, chain_id=1)

    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is None
    assert message == "Unexpected blockchain network."


def test_registered_and_active_issuer_succeeds(monkeypatch):
    _install_fake_web3(monkeypatch, registered=True, active=True)

    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is True
    assert message is None


def test_unregistered_issuer_fails(monkeypatch):
    _install_fake_web3(monkeypatch, registered=False, active=True)

    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is False
    assert message == "Issuer is not registered."


def test_inactive_issuer_fails(monkeypatch):
    _install_fake_web3(monkeypatch, registered=True, active=False)

    result, message = verify_issuer_trust(
        issuer_did=ISSUER_DID,
        rpc_url=RPC_URL,
        registry_address=REGISTRY_ADDRESS,
    )

    assert result is False
    assert message == "Issuer is not active."


def _envelope():
    return {
        "credential": {
            "id": "urn:uuid:test",
            "issuer": ISSUER_DID,
        },
        "proof": {"type": "Eip191PersonalSignature"},
    }


def _stub_other_checks(monkeypatch):
    monkeypatch.setattr(
        engine_module, "verify_signature", lambda c, p: (True, "0xabc")
    )
    monkeypatch.setattr(engine_module, "verify_issuer", lambda i, a: True)
    monkeypatch.setattr(
        engine_module, "verify_expiration", lambda c: (True, None)
    )
    monkeypatch.setattr(
        engine_module, "verify_revocation", lambda c: (True, None)
    )


def test_engine_reports_unknown_when_registry_not_configured(monkeypatch):
    monkeypatch.delenv("ISSUER_REGISTRY_RPC_URL", raising=False)
    monkeypatch.delenv("ISSUER_REGISTRY_ADDRESS", raising=False)
    _stub_other_checks(monkeypatch)

    result = CredentialVerifier().verify(_envelope())

    assert result.checks["issuer_trust"] == "unknown"
    # issuer_trust is informational only: it must not fail the verdict.
    assert result.valid is True
    assert "Issuer registry configuration is missing." in result.errors


def test_engine_reports_failed_when_issuer_not_registered(monkeypatch):
    monkeypatch.setenv("ISSUER_REGISTRY_RPC_URL", RPC_URL)
    monkeypatch.setenv("ISSUER_REGISTRY_ADDRESS", REGISTRY_ADDRESS)
    _stub_other_checks(monkeypatch)
    monkeypatch.setattr(
        engine_module,
        "verify_issuer_trust",
        lambda **kwargs: (False, "Issuer is not registered."),
    )

    result = CredentialVerifier().verify(_envelope())

    assert result.checks["issuer_trust"] is False
    # issuer_trust failure is temporarily excluded from the verdict.
    assert result.valid is True
    assert "Issuer is not registered." in result.errors


def test_engine_reports_success_when_issuer_trusted(monkeypatch):
    monkeypatch.setenv("ISSUER_REGISTRY_RPC_URL", RPC_URL)
    monkeypatch.setenv("ISSUER_REGISTRY_ADDRESS", REGISTRY_ADDRESS)
    _stub_other_checks(monkeypatch)
    monkeypatch.setattr(
        engine_module,
        "verify_issuer_trust",
        lambda **kwargs: (True, None),
    )

    result = CredentialVerifier().verify(_envelope())

    assert result.checks["issuer_trust"] is True
    assert result.valid is True


def test_engine_revoked_credential_stays_invalid(monkeypatch):
    monkeypatch.delenv("ISSUER_REGISTRY_RPC_URL", raising=False)
    monkeypatch.delenv("ISSUER_REGISTRY_ADDRESS", raising=False)
    _stub_other_checks(monkeypatch)
    monkeypatch.setattr(
        engine_module,
        "verify_revocation",
        lambda c: (False, "Credential has been revoked."),
    )

    result = CredentialVerifier().verify(_envelope())

    assert result.checks["issuer_trust"] == "unknown"
    assert result.checks["revocation"] is False
    assert result.valid is False
    assert "Credential has been revoked." in result.errors


def test_engine_invalid_signature_stays_invalid(monkeypatch):
    monkeypatch.delenv("ISSUER_REGISTRY_RPC_URL", raising=False)
    monkeypatch.delenv("ISSUER_REGISTRY_ADDRESS", raising=False)
    _stub_other_checks(monkeypatch)
    monkeypatch.setattr(
        engine_module,
        "verify_signature",
        lambda c, p: (False, None),
    )

    result = CredentialVerifier().verify(_envelope())

    assert result.checks["issuer_trust"] == "unknown"
    assert result.valid is False
    assert "Credential signature is invalid." in result.errors

import base64
import hashlib
import json
from datetime import datetime, timezone
import pytest
from eth_keys import keys
from keepyourid.modules.credentials import service as credential_service_module
from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.credentials.service import (
	CredentialInvalidDataError,
	CredentialService,
)
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization
from eth_account import Account
from eth_account.messages import encode_defunct

TEST_PRIVATE_KEY = keys.PrivateKey(b"\x11" * 32)
ISSUER_ADDRESS = TEST_PRIVATE_KEY.public_key.to_checksum_address()
ISSUER_DID = f"did:ethr:sepolia:{ISSUER_ADDRESS}"
KEY_ID = f"{ISSUER_DID}#controller"
PUBLIC_KEY = TEST_PRIVATE_KEY.public_key.to_hex()


@pytest.fixture
def issuer(db_session):
	organization = Organization(
		legal_name="Test Organization",
		registration_number="TEST-ISSUER-001",
		email="issuer@example.com",
		status=OrganizationStatus.ACTIVE,
	)
	db_session.add(organization)
	db_session.flush()

	did = DID(
		organization_id=organization.id,
		identifier=ISSUER_DID,
		method="ethr",
		document={
			"verificationMethod": [],
			"assertionMethod": [],
		},
		status=DIDStatus.VERIFIED,
	)
	db_session.add(did)
	db_session.commit()
	db_session.refresh(organization)
	return organization


@pytest.fixture
def draft_credential(db_session, issuer):
	service = CredentialService(db_session)
	data = CredentialCreate(
		credential_type="UniversityDegreeCredential",
		subject={
			"id": "did:example:holder",
			"degree": "Computer Science",
		},
		valid_until=datetime(2030, 1, 1, tzinfo=timezone.utc),
	)
	return service.create_draft(issuer.id, data)


@pytest.fixture
def mocked_signing(monkeypatch):
	state = {}

	def resolve_key(self, credential):
		state["payload"] = credential.payload
		return KEY_ID, ISSUER_ADDRESS

	def build_input(payload, key_id):
		assert key_id == KEY_ID
		state["payload"] = payload
		return "header.payload"

	def recover_message(message, signature):
		assert signature == "valid-signature"
		return ISSUER_ADDRESS

	monkeypatch.setattr(
		credential_service_module.IssuerKeyResolver,
		"resolve",
		resolve_key,
	)
	monkeypatch.setattr(
		credential_service_module,
		"build_signing_input",
		build_input,
	)
	monkeypatch.setattr(
		credential_service_module.Account,
		"recover_message",
		recover_message,
	)
	return state


def test_prepare_issuance_success(
	db_session,
	draft_credential,
	mocked_signing,
):
	service = CredentialService(db_session)
	result = service.prepare_issuance(
    draft_credential.id,
    status_list_url=(
        f"https://issuer.example/status-lists/"
        f"{draft_credential.issuer_did_id}"
    ),
)
	assert result["key_id"] == KEY_ID
	assert result["signing_input"] == "header.payload"
	db_session.refresh(draft_credential)
	assert draft_credential.status == CredentialStatus.DRAFT
	assert draft_credential.signed_credential is None


def test_prepare_issuance_rejects_unknown_credential(
	db_session,
):
	from uuid import uuid4

	service = CredentialService(db_session)
	with pytest.raises(CredentialInvalidDataError):
		service.prepare_issuance(uuid4())


def test_complete_issuance_success(
	db_session,
	draft_credential,
	mocked_signing,
):
	service = CredentialService(db_session)
	result = service.complete_issuance(
		credential_id=draft_credential.id,
		signature="valid-signature",
		key_id=KEY_ID,
	)
	assert result.status == CredentialStatus.ISSUED
	assert result.proof is not None
	assert result.proof["signature"] == "valid-signature"
	signed = json.loads(result.signed_credential)
	assert signed["credential"] == result.payload
	assert signed["proof"] == result.proof


def test_complete_issuance_rejects_wrong_key_id(
	db_session,
	draft_credential,
	mocked_signing,
):
	service = CredentialService(db_session)
	with pytest.raises(
		CredentialInvalidDataError,
		match="Signing key does not belong",
	):
		service.complete_issuance(
			credential_id=draft_credential.id,
			signature="valid-signature",
			key_id="did:example:attacker#key-1",
		)
	db_session.refresh(draft_credential)
	assert draft_credential.status == CredentialStatus.DRAFT
	assert draft_credential.signed_credential is None


def test_complete_issuance_rejects_invalid_signature(
	db_session,
	draft_credential,
	mocked_signing,
	monkeypatch,
):
	def reject_signature(message, signature):
		raise ValueError("Invalid signature.")

	monkeypatch.setattr(credential_service_module.Account, "recover_message", reject_signature)
	service = CredentialService(db_session)
	with pytest.raises(
		CredentialInvalidDataError,
		match="signature verification failed",
	):
		service.complete_issuance(
			credential_id=draft_credential.id,
			signature="invalid-signature",
			key_id=KEY_ID,
		)
	db_session.refresh(draft_credential)
	assert draft_credential.status == CredentialStatus.DRAFT
	assert draft_credential.signed_credential is None


def test_complete_issuance_rejects_already_issued_credential(
	db_session,
	draft_credential,
	mocked_signing,
):
	service = CredentialService(db_session)
	service.complete_issuance(
		credential_id=draft_credential.id,
		signature="valid-signature",
		key_id=KEY_ID,
	)
	with pytest.raises(
		CredentialInvalidDataError,
		match="Only draft credentials can be issued",
	):
		service.complete_issuance(
			credential_id=draft_credential.id,
			signature="another-signature",
			key_id=KEY_ID,
		)


def test_get_issuer_signing_key_success(
	db_session,
	draft_credential,
	mocked_signing,
):
	service = CredentialService(db_session)
	key_id, public_key = service.get_issuer_signing_key(
		draft_credential.id
	)
	assert key_id == KEY_ID
	assert public_key == ISSUER_ADDRESS


def test_get_issued_credential_returns_signed_value(
	db_session,
	draft_credential,
	mocked_signing,
):
	service = CredentialService(db_session)
	issued = service.complete_issuance(
		credential_id=draft_credential.id,
		signature="valid-signature",
		key_id=KEY_ID,
	)
	retrieved = service.get(draft_credential.id)
	assert retrieved is not None
	assert retrieved.status == CredentialStatus.ISSUED
	assert retrieved.signed_credential == issued.signed_credential
	signed = json.loads(retrieved.signed_credential)
	assert signed["credential"] == retrieved.payload
	assert signed["proof"] == retrieved.proof


def _b64url_encode(data: bytes) -> str:
	return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_real_secp256k1_signing_material():
	private_key = keys.PrivateKey(b"\x11" * 32)
	public_key = private_key.public_key.to_hex()
	key_id = f"{ISSUER_DID}#controller"
	return private_key, public_key, key_id


def test_verify_jws_with_real_secp256k1_key():
	private_key, public_key, key_id = _generate_real_secp256k1_signing_material()
	payload = {
		"@context": ["https://www.w3.org/ns/credentials/v2"],
		"id": "urn:uuid:1234",
		"type": ["VerifiableCredential", "UniversityDegreeCredential"],
		"issuer": ISSUER_DID,
		"credentialSubject": {"id": "did:example:holder"},
	}
	header = {"alg": "ES256K", "typ": "vc+jwt", "cty": "vc", "kid": key_id}
	encoded_header = _b64url_encode(
		json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
	)
	encoded_payload = _b64url_encode(
		json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
	)
	signing_input = f"{encoded_header}.{encoded_payload}"
	digest = hashlib.sha256(signing_input.encode("ascii")).digest()
	signature = private_key.sign_msg_hash(digest)
	jws = f"{signing_input}.{_b64url_encode(signature[:-1])}"

	assert credential_service_module.verify_jws(jws, public_key, key_id) == payload

	with pytest.raises(credential_service_module.JWSVerificationError, match="Invalid credential signature"):
		credential_service_module.verify_jws(
			f"{signing_input}.{_b64url_encode(b'0' * 64)}",
			public_key,
			key_id,
		)

	modified_payload = dict(payload)
	modified_payload["credentialSubject"] = {"id": "did:example:holder-2"}
	modified_encoded = _b64url_encode(
		json.dumps(modified_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
	)
	modified_jws = f"{encoded_header}.{modified_encoded}.{_b64url_encode(signature[:-1])}"
	with pytest.raises(credential_service_module.JWSVerificationError):
		credential_service_module.verify_jws(modified_jws, public_key, key_id)

	modified_header = dict(header)
	modified_header["kid"] = f"{ISSUER_DID}#other"
	modified_encoded_header = _b64url_encode(
		json.dumps(modified_header, separators=(",", ":"), sort_keys=True).encode("utf-8")
	)
	modified_header_jws = f"{modified_encoded_header}.{encoded_payload}.{_b64url_encode(signature[:-1])}"
	with pytest.raises(credential_service_module.JWSVerificationError, match="Unexpected issuer key identifier"):
		credential_service_module.verify_jws(modified_header_jws, public_key, key_id)

	with pytest.raises(credential_service_module.JWSVerificationError, match="Invalid signature length"):
		credential_service_module.complete_jws(signing_input, _b64url_encode(b"\x00" * 63))

	with pytest.raises(credential_service_module.JWSVerificationError, match="Invalid compact JWS format"):
		credential_service_module.verify_jws("definitely.not.a.valid.jws", public_key, key_id)


def test_issuance_prepare_and_complete_are_organization_scoped(db_session):
	issuer_org = Organization(
		legal_name="Issuer Org",
		registration_number="ORG-001",
		email="issuer@example.com",
		status=OrganizationStatus.ACTIVE,
	)
	other_org = Organization(
		legal_name="Other Org",
		registration_number="ORG-002",
		email="other@example.com",
		status=OrganizationStatus.ACTIVE,
	)
	db_session.add_all([issuer_org, other_org])
	db_session.flush()

	private_key = TEST_PRIVATE_KEY
	public_key_hex = private_key.public_key.to_hex()

	issuer_did = DID(
		organization_id=issuer_org.id,
		identifier=ISSUER_DID,
		method="ethr",
		document={
			"verificationMethod": [{
				"id": KEY_ID,
				"type": "EcdsaSecp256k1VerificationKey2019",
				"controller": ISSUER_DID,
				"publicKeyHex": public_key_hex,
     			"blockchainAccountId": f"eip155:11155111:{ISSUER_ADDRESS}",
			}],
			"assertionMethod": [KEY_ID],
		},
		status=DIDStatus.VERIFIED,
	)
	db_session.add(issuer_did)
	db_session.flush()

	service = CredentialService(db_session)
	credential = service.create_draft(
		issuer_org.id,
		CredentialCreate(
			credential_type="UniversityDegreeCredential",
			subject={"id": "did:example:holder", "degree": "Computer Science"},
			valid_until=datetime(2030, 1, 1, tzinfo=timezone.utc),
		),
	)

	from fastapi.testclient import TestClient
	from keepyourid.core.dependencies import get_db
	from keepyourid.main import app

	app.dependency_overrides[get_db] = lambda: db_session
	try:
		with TestClient(app) as client:
			prepare_response = client.post(
				f"/api/v1/organizations/{issuer_org.id}/credentials/{credential.id}/prepare-issuance"
			)
			
			print("PREPARE STATUS:", prepare_response.status_code)
			print("PREPARE BODY:", prepare_response.text)
			assert prepare_response.status_code == 200
			payload = prepare_response.json()
			assert payload["key_id"] == KEY_ID

			signing_input = payload["signing_input"]
			signature = Account.sign_message(
				encode_defunct(text=signing_input),
				private_key=private_key.to_bytes(),
			).signature.hex()
   
			status_list_signing_input = payload["status_list_signing_input"]

			status_list_signature = Account.sign_message(
				encode_defunct(text=status_list_signing_input),
				private_key=private_key.to_bytes(),
			).signature.hex()

			status_list_signing_input = payload["status_list_signing_input"]

			status_list_signature = Account.sign_message(
				encode_defunct(text=status_list_signing_input),
				private_key=private_key.to_bytes(),
			).signature.hex()

			complete_response = client.post(
				f"/api/v1/organizations/{issuer_org.id}/credentials/{credential.id}/complete-issuance",
				json={
					"signature": signature,
					"status_list_signature": status_list_signature,
					"key_id": KEY_ID,
				},
			)

			print("COMPLETE STATUS:", complete_response.status_code)
			print("COMPLETE BODY:", complete_response.text)

			assert complete_response.status_code == 200
			assert complete_response.json()["status"] == CredentialStatus.ISSUED.value

			cross_org_response = client.post(
				f"/api/v1/organizations/{other_org.id}/credentials/{credential.id}/prepare-issuance"
			)
			assert cross_org_response.status_code == 404

			second_complete = client.post(
				f"/api/v1/organizations/{issuer_org.id}/credentials/{credential.id}/complete-issuance",
				json={
					"signature": signature,
					"status_list_signature": status_list_signature,
					"key_id": KEY_ID,
				},
			)
			assert second_complete.status_code == 422
	finally:
		app.dependency_overrides.clear()

import base64
import gzip
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from eth_utils import is_address, to_checksum_address

from keepyourid_verifier.checks.signature import verify_signature

MINIMUM_BITSTRING_SIZE = 16 * 1024


def _fetch_status_list(url: str) -> dict:
	parsed = urlparse(url)

	if parsed.scheme not in {"http", "https"} or not parsed.netloc:
		raise ValueError("Invalid status list URL.")

	request = Request(
		url,
		headers={"Accept": "application/json"},
		method="GET",
	)

	with urlopen(request, timeout=10) as response:
		if response.status != 200:
			raise ValueError("Unable to retrieve status list.")

		if int(response.headers.get("Content-Length", 0) or 0) > 2_000_000:
			raise ValueError("Status list response is too large.")

		data = response.read(2_000_001)

		if len(data) > 2_000_000:
			raise ValueError("Status list response is too large.")

	return json.loads(data)


def _decode_bitstring(encoded_list: str) -> bytes:
	# Multibase base64url encoding uses the "u" prefix.
	if not encoded_list.startswith("u"):
		raise ValueError("Unsupported multibase encoding.")

	encoded = encoded_list[1:]
	padding = "=" * (-len(encoded) % 4)

	compressed = base64.urlsafe_b64decode(encoded + padding)
	bitstring = gzip.decompress(compressed)

	if len(bitstring) < MINIMUM_BITSTRING_SIZE:
		raise ValueError("Status list is smaller than 16 KB.")

	return bitstring


def verify_revocation(
	credential: dict,
) -> tuple[bool | None, str | None]:

	credential_status = credential.get("credentialStatus")

	if not credential_status:
		return None, "Credential has no credentialStatus entry."

	# The W3C model permits one entry or an array of entries.
	entries = (
		credential_status
		if isinstance(credential_status, list)
		else [credential_status]
	)

	revocation_entries = [
		entry
		for entry in entries
		if isinstance(entry, dict)
		and entry.get("statusPurpose") == "revocation"
	]

	if not revocation_entries:
		return None, "No revocation status entry found."

	for entry in revocation_entries:
		if entry.get("type") != "BitstringStatusListEntry":
			return False, "Unsupported credential status type."

		try:
			index = int(entry["statusListIndex"])

			if index < 0:
				raise ValueError("Negative status index.")

			status_url = entry["statusListCredential"]

			status_list = _fetch_status_list(status_url)
			
			signed_payload = status_list.get("credential")
			proof = status_list.get("proof")

			if not isinstance(signed_payload, dict):
				raise ValueError("Missing signed status list credential.")

			if not isinstance(proof, dict):
				raise ValueError("Missing status list proof.")

			# The status list must belong to the same issuer
			# as the verifiable credential.
			if signed_payload.get("issuer") != credential.get("issuer"):
				raise ValueError("Status list issuer mismatch.")

			# Verify the issuer's cryptographic signature.
			signature_valid, recovered_address = verify_signature(
				signed_payload,
				proof,
			)

			if not signature_valid or not recovered_address:
				raise ValueError("Invalid status list signature.")

			issuer_did = signed_payload.get("issuer", "")
			expected_address = issuer_did.rsplit(":", 1)[-1]

			if not is_address(expected_address):
				raise ValueError("Invalid status list issuer DID.")

			if (
				to_checksum_address(recovered_address)
				!= to_checksum_address(expected_address)
			):
				raise ValueError("Status list signer does not match issuer DID.")

			# Continue verification using the authenticated payload.
			status_list = signed_payload

			list_types = status_list.get("type", [])
			if isinstance(list_types, str):
				list_types = [list_types]

			if "BitstringStatusListCredential" not in list_types:
				raise ValueError("Invalid status list credential type.")

			subject = status_list.get("credentialSubject", {})

			if subject.get("type") != "BitstringStatusList":
				raise ValueError("Invalid bitstring subject type.")

			if subject.get("statusPurpose") != "revocation":
				raise ValueError("Status purpose mismatch.")

			bitstring = _decode_bitstring(subject["encodedList"])

			if index >= len(bitstring) * 8:
				raise ValueError("Status index is out of range.")

			# W3C: index 0 is the left-most bit.
			byte_index = index // 8
			bit_offset = index % 8
			revoked = bool(
				bitstring[byte_index] & (1 << (7 - bit_offset))
			)

			if revoked:
				return False, "Credential has been revoked."

		except (KeyError, TypeError, ValueError, OSError,
				HTTPError, URLError, json.JSONDecodeError) as exc:
			return False, f"Revocation verification failed: {exc}"

	return True, None

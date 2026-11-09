import { API_BASE_URL, apiRequest } from "./api";

export function getCredentialPresentationUrl(credentialId) {
  return `${API_BASE_URL}/verifications/presentation/${encodeURIComponent(
    credentialId
  )}`;
}

export async function fetchCredentialPresentation(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });

  if (!response.ok) {
    const error = new Error(`Erreur API (${response.status})`);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export function verifyCredential(signedCredential) {
  return apiRequest("/verifications", {
    method: "POST",
    body: JSON.stringify({
      signed_credential: signedCredential,
    }),
  });
}

import { apiRequest } from "./api";

export function getCredentials(organizationId) {
  return apiRequest(`/organizations/${organizationId}/credentials`);
}

export function createCredential(organizationId, payload) {
  return apiRequest(`/organizations/${organizationId}/credentials`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCredential(organizationId, credentialId) {
  return apiRequest(
    `/organizations/${organizationId}/credentials/${credentialId}`
  );
}

export function revokeCredential(organizationId, credentialId, reason) {
  return apiRequest(
    `/organizations/${organizationId}/credentials/${credentialId}/revoke`,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    }
  );
}
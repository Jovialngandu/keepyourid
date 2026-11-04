
import { apiRequest } from "./api";

export function getOrganizationDids(organizationId) {
  return apiRequest(
    `/organizations/${encodeURIComponent(organizationId)}/dids`
  );
}

export function createDID(organizationId, payload) {
  return apiRequest(
    `/dids/organizations/${encodeURIComponent(organizationId)}`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function createDIDChallenge(didId, payload) {
  return apiRequest(
    `/dids/${encodeURIComponent(didId)}/challenges`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function verifyDID(didId, payload) {
  return apiRequest(
    `/dids/${encodeURIComponent(didId)}/verify`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}



export function registerIssuer(organizationId, payload = {}) {
  return apiRequest(
    `/issuers/organizations/${encodeURIComponent(organizationId)}/register`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

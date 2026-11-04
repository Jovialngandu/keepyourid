
import { apiRequest } from "./api";

export function getOrganization(organizationId) {
  return apiRequest(
    `/organizations/${encodeURIComponent(organizationId)}`
  );
}

export function getOrganizationDids(organizationId) {
  return apiRequest(
    `/organizations/${encodeURIComponent(organizationId)}/dids`
  );
}

export function getOrganizationCredentials(organizationId) {
  return apiRequest(
    `/organizations/${encodeURIComponent(organizationId)}/credentials`
  );
}

export function getOrganizationTransactions(organizationId) {
  return apiRequest(
    `/organizations/${encodeURIComponent(organizationId)}/transactions`
  );
}

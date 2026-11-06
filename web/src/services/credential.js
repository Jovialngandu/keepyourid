// import { apiRequest } from "./api";

// // export function getCredentials(organizationId) {
// //   return apiRequest(`/organizations/${organizationId}/credentials`);
// // }

// // export function createCredential(organizationId, payload) {
// //   return apiRequest(`/organizations/${organizationId}/credentials`, {
// //     method: "POST",
// //     body: JSON.stringify(payload),
// //   });
// // }

// // export function getCredential(organizationId, credentialId) {
// //   return apiRequest(
// //     `/organizations/${organizationId}/credentials/${credentialId}`
// //   );
// // }

// // export function revokeCredential(organizationId, credentialId, reason) {
// //   return apiRequest(
// //     `/organizations/${organizationId}/credentials/${credentialId}/revoke`,
// //     {
// //       method: "POST",
// //       body: JSON.stringify({ reason }),
// //     }
// //   );
// // }



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

export function prepareCredentialIssuance(organizationId, credentialId) {
  return apiRequest(
    `/organizations/${organizationId}/credentials/${credentialId}/prepare-issuance`,
    { method: "POST" }
  );
}

export function completeCredentialIssuance(
  organizationId,
  credentialId,
  payload
) {
  return apiRequest(
    `/organizations/${organizationId}/credentials/${credentialId}/complete-issuance`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

// export function revokeCredential(organizationId, credentialId, reason) {
//   return apiRequest(
//     `/organizations/${organizationId}/credentials/${credentialId}/revoke`,
//     {
//       method: "POST",
//       body: JSON.stringify({ reason }),
//     }
//   );
// }



export function prepareCredentialRevocation(
  organizationId,
  credentialId
) {
  return apiRequest(
    `/organizations/${organizationId}/credentials/${credentialId}/prepare-revocation`,
    { method: "POST" }
  );
}

export function completeCredentialRevocation(
  organizationId,
  credentialId,
  payload
) {
  return apiRequest(
    `/organizations/${organizationId}/credentials/${credentialId}/complete-revocation`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}






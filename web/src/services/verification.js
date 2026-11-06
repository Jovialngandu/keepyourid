import { apiRequest } from "./api";

export function verifyCredential(signedCredential) {
  return apiRequest("/verifications", {
    method: "POST",
    body: JSON.stringify({
      signed_credential: signedCredential,
    }),
  });
}

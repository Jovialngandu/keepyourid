
import { apiRequest } from "./api";

// Récupérer les DID associés à l'utilisateur connecté.
export async function getHolderDIDs() {
  return apiRequest("/holders/me/dids");
}

// Associer un DID au compte utilisateur.
export async function registerHolderDID(data) {
  return apiRequest("/holders/me/dids", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Demander un challenge de vérification.
export async function createHolderDIDChallenge(didId, data) {
  return apiRequest(`/holders/me/dids/${didId}/challenges`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Soumettre la preuve signée par MetaMask.
export async function verifyHolderDID(didId, data) {
  return apiRequest(`/holders/me/dids/${didId}/verify`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Récupérer les credentials du titulaire connecté.
export async function getHolderCredentials() {
  return apiRequest("/holders/me/credentials");
}

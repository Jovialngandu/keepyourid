export function getCredentialQrValue(credential) {
  const value = credential?.signed_credential;

  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (value && typeof value === "object") {
    return JSON.stringify(value);
  }

  return "";
}

export function isSignedCredentialEnvelope(value) {
  return (
    Boolean(value) &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Boolean(value.credential) &&
    typeof value.credential === "object" &&
    Boolean(value.proof) &&
    typeof value.proof === "object"
  );
}

function parseJsonString(value) {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

export function normalizeVerificationInput(input) {
  let parsed = input;

  if (typeof parsed === "string") {
    const trimmed = parsed.trim();

    if (!trimmed) {
      throw new Error("Le contenu scanné ou importé est vide.");
    }

    try {
      parsed = JSON.parse(trimmed);
    } catch {
      throw new Error(
        "Le contenu scanné ou importé n'est pas du JSON valide."
      );
    }
  }

  if (typeof parsed === "string") {
    parsed = parseJsonString(parsed);
  }

  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    if (Object.prototype.hasOwnProperty.call(parsed, "signed_credential")) {
      return parsed.signed_credential;
    }

    if (isSignedCredentialEnvelope(parsed)) {
      return parsed;
    }

    throw new Error(
      "Format de credential non reconnu : signed_credential, credential et proof sont requis."
    );
  }

  if (typeof parsed === "string" && parsed.trim()) {
    return parsed;
  }

  throw new Error("Format de credential non reconnu.");
}

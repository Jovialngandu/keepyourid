import { describe, expect, it } from "vitest";

import {
  getCredentialQrValue,
  isSignedCredentialEnvelope,
  normalizeVerificationInput,
} from "./verification";

const envelope = {
  credential: {
    id: "urn:uuid:test",
    issuer: "did:ethr:sepolia:0x1111111111111111111111111111111111111111",
  },
  proof: {
    type: "Eip191PersonalSignature",
    verificationMethod:
      "did:ethr:sepolia:0x1111111111111111111111111111111111111111#controller",
    signer: "0x1111111111111111111111111111111111111111",
    signature: "0x" + "ab".repeat(65),
  },
};

describe("getCredentialQrValue", () => {
  it("returns the signed_credential string", () => {
    const credential = {
      id: "sql-record-id",
      credential_id: "urn:uuid:test",
      signed_credential: JSON.stringify(envelope),
    };

    expect(getCredentialQrValue(credential)).toBe(
      JSON.stringify(envelope)
    );
  });

  it("returns an empty value when signed_credential is missing", () => {
    expect(getCredentialQrValue({ id: "sql-record-id" })).toBe("");
    expect(getCredentialQrValue(null)).toBe("");
  });

  it("stringifies an object signed_credential", () => {
    const credential = { signed_credential: envelope };

    expect(JSON.parse(getCredentialQrValue(credential))).toEqual(envelope);
  });
});

describe("isSignedCredentialEnvelope", () => {
  it("accepts credential and proof objects", () => {
    expect(isSignedCredentialEnvelope(envelope)).toBe(true);
  });

  it("rejects incomplete envelopes", () => {
    expect(isSignedCredentialEnvelope({ credential: {} })).toBe(false);
    expect(isSignedCredentialEnvelope(null)).toBe(false);
  });
});

describe("normalizeVerificationInput", () => {
  it("accepts an envelope object", () => {
    expect(normalizeVerificationInput(envelope)).toEqual(envelope);
  });

  it("accepts a request object", () => {
    expect(
      normalizeVerificationInput({ signed_credential: envelope })
    ).toEqual(envelope);
  });

  it("accepts a JSON string envelope", () => {
    expect(normalizeVerificationInput(JSON.stringify(envelope))).toEqual(
      envelope
    );
  });

  it("accepts a JSON string request", () => {
    expect(
      normalizeVerificationInput(
        JSON.stringify({ signed_credential: envelope })
      )
    ).toEqual(envelope);
  });

  it("keeps a signed_credential JSON string as string", () => {
    const raw = JSON.stringify(envelope);

    expect(
      normalizeVerificationInput({ signed_credential: raw })
    ).toBe(raw);
  });

  it("rejects invalid JSON", () => {
    expect(() => normalizeVerificationInput("not json")).toThrow(
      "n'est pas du JSON valide"
    );
  });

  it("rejects objects without credential or proof", () => {
    expect(() => normalizeVerificationInput({ foo: "bar" })).toThrow(
      "Format de credential non reconnu"
    );
  });
});

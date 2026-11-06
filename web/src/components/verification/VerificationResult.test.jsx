import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import VerificationResult from "./VerificationResult";

const validResult = {
  valid: true,
  credential_id: "urn:uuid:test",
  issuer: "did:ethr:sepolia:0x1111111111111111111111111111111111111111",
  checks: {
    signature: true,
    issuer_did: true,
    issuer_trust: true,
    revocation: true,
    expiration: true,
  },
  errors: [],
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("VerificationResult", () => {
  it("shows a successful verdict", () => {
    render(<VerificationResult result={validResult} />);

    expect(screen.getByText("Vérification réussie")).toBeTruthy();
    expect(screen.getByText("urn:uuid:test")).toBeTruthy();
    expect(screen.getAllByText("Réussi")).toHaveLength(5);
  });

  it("shows a failed verdict without claiming the credential is valid", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    render(
      <VerificationResult
        result={{
          ...validResult,
          valid: false,
          checks: { ...validResult.checks, signature: false },
          errors: ["Credential signature is invalid."],
        }}
      />
    );

    expect(screen.getByText("Vérification échouée")).toBeTruthy();
    expect(screen.queryByText(/Credential valide/i)).toBeNull();
    expect(screen.getByText("Échoué")).toBeTruthy();
    // Errors are logged to the console, not displayed in the UI.
    expect(screen.queryByText("Credential signature is invalid.")).toBeNull();
    expect(warn).toHaveBeenCalledWith("Credential signature is invalid.");
  });

  it("shows non-applicable checks as null", () => {
    render(
      <VerificationResult
        result={{
          ...validResult,
          checks: { ...validResult.checks, revocation: null },
        }}
      />
    );

    expect(screen.getByText("Non applicable")).toBeTruthy();
  });

  it("shows unknown checks as Inconnu without failing the verdict", () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});

    render(
      <VerificationResult
        result={{
          ...validResult,
          checks: { ...validResult.checks, issuer_trust: "unknown" },
          errors: ["Issuer registry configuration is missing."],
        }}
      />
    );

    expect(screen.getByText("Vérification réussie")).toBeTruthy();
    expect(screen.getByText("Inconnu")).toBeTruthy();
    expect(
      screen.queryByText("Issuer registry configuration is missing.")
    ).toBeNull();
  });

  it("shows invalid input errors", () => {
    render(
      <VerificationResult
        error={{ kind: "invalid", message: "Le JSON est invalide." }}
      />
    );

    expect(screen.getByText("Entrée invalide")).toBeTruthy();
    expect(screen.getByText("Le JSON est invalide.")).toBeTruthy();
  });

  it("shows technical errors", () => {
    render(
      <VerificationResult
        error={{
          kind: "technical",
          message: "Erreur API (500)",
          status: 500,
        }}
      />
    );

    expect(screen.getByText("Erreur technique")).toBeTruthy();
    expect(screen.getByText("Erreur API (500)")).toBeTruthy();
    expect(screen.getByText("Code HTTP : 500")).toBeTruthy();
  });

  it("shows a revoked credential as failed", () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});

    render(
      <VerificationResult
        result={{
          ...validResult,
          valid: false,
          checks: { ...validResult.checks, revocation: false },
          errors: ["Credential is revoked."],
        }}
      />
    );

    expect(screen.getByText("Vérification échouée")).toBeTruthy();
    expect(screen.queryByText("Credential is revoked.")).toBeNull();
    expect(screen.getByText("Révocation")).toBeTruthy();
    expect(screen.getByText("Échoué")).toBeTruthy();
  });
});

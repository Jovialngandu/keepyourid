import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Verify from "./Verify";
import { verifyCredential } from "../services/verification";

vi.mock("../services/verification", () => ({
  verifyCredential: vi.fn(),
}));

vi.mock("../components/layout/Navbar", () => ({
  default: () => <div>Navbar</div>,
}));

vi.mock("../components/layout/Footer", () => ({
  default: () => <div>Footer</div>,
}));

vi.mock("../components/verification/QrScanner", () => ({
  default: ({ onScan }) => (
    <button
      type="button"
      onClick={() =>
        onScan(
          JSON.stringify({
            credential: { id: "urn:uuid:test" },
            proof: { type: "Eip191PersonalSignature" },
          })
        )
      }
    >
      Simuler scan
    </button>
  ),
}));

const envelope = {
  credential: { id: "urn:uuid:test" },
  proof: { type: "Eip191PersonalSignature" },
};

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

function scanCredential() {
  fireEvent.click(screen.getByRole("button", { name: "Ouvrir la caméra" }));
  fireEvent.click(screen.getByRole("button", { name: "Simuler scan" }));
}

describe("Verify page", () => {
  beforeEach(() => {
    verifyCredential.mockReset();
  });

  it("verifies a scanned credential and shows the result", async () => {
    verifyCredential.mockResolvedValue(validResult);

    render(<Verify />);
    scanCredential();

    expect(verifyCredential).toHaveBeenCalledWith(envelope);
    expect(await screen.findByText("Vérification réussie")).toBeTruthy();
  });

  it("shows a failed verification without claiming validity", async () => {
    verifyCredential.mockResolvedValue({
      ...validResult,
      valid: false,
      checks: { ...validResult.checks, signature: false },
      errors: ["Credential signature is invalid."],
    });

    render(<Verify />);
    scanCredential();

    expect(await screen.findByText("Vérification échouée")).toBeTruthy();
    expect(screen.queryByText(/Credential valide/i)).toBeNull();
    expect(
      screen.getByText("Credential signature is invalid.")
    ).toBeTruthy();
  });

  it("imports a JSON file and verifies it", async () => {
    verifyCredential.mockResolvedValue(validResult);

    render(<Verify />);

    const file = new File(
      [JSON.stringify({ signed_credential: envelope })],
      "credential.json",
      { type: "application/json" }
    );

    fireEvent.change(screen.getByTestId("verification-file-input"), {
      target: { files: [file] },
    });

    expect(await screen.findByText("Vérification réussie")).toBeTruthy();
    expect(verifyCredential).toHaveBeenCalledWith(envelope);
  });

  it.each([
    [422, "Entrée invalide"],
    [429, "Erreur technique"],
    [500, "Erreur technique"],
  ])("maps HTTP %s to %s", async (status, title) => {
    verifyCredential.mockRejectedValue(
      Object.assign(new Error(`Erreur API (${status})`), { status })
    );

    render(<Verify />);
    scanCredential();

    expect(await screen.findByText(title)).toBeTruthy();
    expect(screen.getByText(`Code HTTP : ${status}`)).toBeTruthy();
  });

  it("maps network errors to a technical error", async () => {
    verifyCredential.mockRejectedValue(new TypeError("Failed to fetch"));

    render(<Verify />);
    scanCredential();

    expect(await screen.findByText("Erreur technique")).toBeTruthy();
    expect(screen.getByText("Failed to fetch")).toBeTruthy();
  });
});

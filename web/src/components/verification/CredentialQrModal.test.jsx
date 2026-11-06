import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import CredentialQrModal from "./CredentialQrModal";

vi.mock("react-qr-code", () => ({
  default: ({ value }) => (
    <span data-testid="qr-value">{value}</span>
  ),
}));

const signedCredential = JSON.stringify({
  credential: { id: "urn:uuid:test" },
  proof: { type: "Eip191PersonalSignature" },
});

const credential = {
  id: "sql-record-id",
  credential_id: "urn:uuid:test",
  signed_credential: signedCredential,
};

describe("CredentialQrModal", () => {
  it("renders the QR value from signed_credential only", () => {
    render(<CredentialQrModal credential={credential} onClose={vi.fn()} />);

    expect(screen.getByTestId("qr-value").textContent).toBe(
      signedCredential
    );
    expect(screen.queryByText("sql-record-id")).toBeNull();
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();

    render(<CredentialQrModal credential={credential} onClose={onClose} />);

    fireEvent.click(screen.getByLabelText("Fermer le QR code"));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("copies the signed_credential JSON", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);

    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    render(<CredentialQrModal credential={credential} onClose={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Copier le JSON" }));

    expect(await screen.findByText("JSON copié")).toBeTruthy();
    expect(writeText).toHaveBeenCalledWith(signedCredential);
  });
});

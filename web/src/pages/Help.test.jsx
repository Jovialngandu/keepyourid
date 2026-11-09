import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Help from "./Help";

vi.mock("../components/layout/Navbar", () => ({
  default: () => <div>Navbar</div>,
}));

vi.mock("../components/layout/Footer", () => ({
  default: () => <div>Footer</div>,
}));

function renderHelp() {
  return render(
    <MemoryRouter>
      <Help />
    </MemoryRouter>
  );
}

describe("Help page", () => {
  it("shows the issuer guide by default", () => {
    renderHelp();

    expect(screen.getByRole("heading", { name: /Organisateur/ })).toBeTruthy();
    expect(
      screen.getByText(/Créer un compte & se connecter/)
    ).toBeTruthy();
  });

  it("switches to the verifier steps when the tab is clicked", () => {
    renderHelp();

    fireEvent.click(screen.getByRole("tab", { name: /Vérificateur/ }));

    expect(
      screen.getByText(/Accéder à l'espace de vérification/)
    ).toBeTruthy();
    expect(screen.getByRole("link", { name: /Vérifier/ })).toBeTruthy();
  });

  it("switches to the holder steps", () => {
    renderHelp();

    fireEvent.click(
      screen.getByRole("tab", { name: /Client \(Titulaire\)/ })
    );

    expect(
      screen.getByText(/Connecter MetaMask sur Sepolia/)
    ).toBeTruthy();
    expect(
      screen.getByText(/Présenter par QR code/)
    ).toBeTruthy();
  });
});

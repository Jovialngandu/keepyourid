import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./AuthContext";
import { getAccessToken } from "../services/api";

function Probe() {
  const { user, loading, login, logout } = useAuth();

  if (loading) {
    return <div>loading</div>;
  }

  return (
    <div>
      <span data-testid="user">{user ? user.email : "anonymous"}</span>
      <button onClick={() => login({ email: "a@b.com", password: "password123" })}>
        login
      </button>
      <button onClick={logout}>logout</button>
    </div>
  );
}

function jsonResponse(body, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  };
}

describe("AuthContext session persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("restores the session from the stored token after reload", async () => {
    localStorage.setItem("keepyourid_access_token", "stored-token");
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ id: "1", email: "user@example.com", full_name: "User" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("user").textContent).toBe("user@example.com"),
    );

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer stored-token");
  });

  it("stores the access token on login", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "Authentication required." }, false, 401))
      .mockResolvedValueOnce(
        jsonResponse({
          user: { id: "1", email: "a@b.com", full_name: "A" },
          access_token: "new-token",
          token_type: "bearer",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("user").textContent).toBe("anonymous"),
    );

    await userEvent.click(screen.getByText("login"));

    await waitFor(() => expect(getAccessToken()).toBe("new-token"));
    expect(screen.getByTestId("user").textContent).toBe("a@b.com");
  });

  it("clears the token and user on logout", async () => {
    localStorage.setItem("keepyourid_access_token", "stored-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ id: "1", email: "user@example.com", full_name: "User" }),
      )
      .mockResolvedValueOnce(jsonResponse({ success: true }));
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("user").textContent).toBe("user@example.com"),
    );

    await userEvent.click(screen.getByText("logout"));

    await waitFor(() => expect(getAccessToken()).toBeNull());
    expect(screen.getByTestId("user").textContent).toBe("anonymous");

    const logoutCall = fetchMock.mock.calls[1];
    expect(logoutCall[1].headers.Authorization).toBe("Bearer stored-token");
  });
});

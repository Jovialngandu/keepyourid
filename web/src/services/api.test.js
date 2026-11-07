import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest, getAccessToken, setAccessToken } from "./api";

function mockFetchOk(body = {}) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(body),
  });
}

describe("access token storage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("stores and reads the token from localStorage", () => {
    setAccessToken("token-123");
    expect(getAccessToken()).toBe("token-123");
    expect(localStorage.getItem("keepyourid_access_token")).toBe("token-123");
  });

  it("clears the token", () => {
    setAccessToken("token-123");
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });
});

describe("apiRequest Authorization header", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("sends Bearer token when one is stored", async () => {
    setAccessToken("secret-token");
    const fetchMock = mockFetchOk({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/auth/me");

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer secret-token");
    expect(init.credentials).toBe("include");
  });

  it("omits Authorization header when no token is stored", async () => {
    const fetchMock = mockFetchOk({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/auth/me");

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });
});

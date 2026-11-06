import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "./api";
import { verifyCredential } from "./verification";

vi.mock("./api", () => ({
  apiRequest: vi.fn(),
}));

const envelope = {
  credential: { id: "urn:uuid:test" },
  proof: { type: "Eip191PersonalSignature" },
};

describe("verifyCredential", () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it("posts signed_credential to /verifications", async () => {
    apiRequest.mockResolvedValue({ valid: true });

    await verifyCredential(envelope);

    expect(apiRequest).toHaveBeenCalledWith("/verifications", {
      method: "POST",
      body: JSON.stringify({ signed_credential: envelope }),
    });
  });

  it("supports a JSON string signed_credential", async () => {
    apiRequest.mockResolvedValue({ valid: false });
    const raw = JSON.stringify(envelope);

    await verifyCredential(raw);

    expect(apiRequest).toHaveBeenCalledWith("/verifications", {
      method: "POST",
      body: JSON.stringify({ signed_credential: raw }),
    });
  });
});

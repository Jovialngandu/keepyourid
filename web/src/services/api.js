
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });

  const result = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = result?.detail;

    const message = Array.isArray(detail)
      ? detail.map((error) => error.msg).join(", ")
      : typeof detail === "string"
        ? detail
        : `Erreur API (${response.status})`;

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return result;
}

export async function createOrganization(data) {
  return apiRequest("/organizations/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

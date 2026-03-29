import { CAPTURE_ENDPOINT, QUEUE_ENDPOINT, RESPONSE_STATUS_TEXTS } from "./protocol.js";

const BACKEND_UNAVAILABLE = "backend_unavailable";

export function resolveBackendBaseUrl() {
  const manifest = chrome.runtime.getManifest();
  const hostPermission = manifest.host_permissions.find((value) =>
    typeof value === "string" && value.startsWith("http://127.0.0.1:")
  );

  if (!hostPermission) {
    return null;
  }

  return hostPermission.replace(/\/\*$/, "");
}

export async function captureSelection(baseUrl, payload) {
  const endpointUrl = `${baseUrl}${CAPTURE_ENDPOINT}`;

  try {
    const response = await fetch(endpointUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    try {
      return await response.json();
    } catch {
      return {
        status: BACKEND_UNAVAILABLE,
        message: RESPONSE_STATUS_TEXTS[BACKEND_UNAVAILABLE] || "本地后端不可用",
      };
    }
  } catch {
    return {
      status: BACKEND_UNAVAILABLE,
      message: RESPONSE_STATUS_TEXTS[BACKEND_UNAVAILABLE] || "本地后端不可用",
    };
  }
}

export async function fetchQueue(baseUrl) {
  if (!baseUrl) {
    throw new Error(RESPONSE_STATUS_TEXTS[BACKEND_UNAVAILABLE] || "本地后端不可用");
  }

  const endpointUrl = `${baseUrl}${QUEUE_ENDPOINT}`;
  const response = await fetch(endpointUrl, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Queue request failed with status ${response.status} at ${QUEUE_ENDPOINT}.`);
  }

  return await response.json();
}

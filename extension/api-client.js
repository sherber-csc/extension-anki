import { CAPTURE_ENDPOINT, RESPONSE_STATUS_TEXTS } from "./protocol.js";

const BACKEND_UNAVAILABLE = "backend_unavailable";

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

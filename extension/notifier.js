import { RESPONSE_STATUS_TEXTS } from "./protocol.js";

const DEFAULT_MESSAGE = "操作完成";

export function getNotificationText(status, fallbackMessage) {
  if (status && Object.prototype.hasOwnProperty.call(RESPONSE_STATUS_TEXTS, status)) {
    return RESPONSE_STATUS_TEXTS[status];
  }

  if (typeof fallbackMessage === "string" && fallbackMessage.trim()) {
    return fallbackMessage.trim();
  }

  return DEFAULT_MESSAGE;
}

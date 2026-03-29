import { captureSelection, resolveBackendBaseUrl } from "./api-client.js";
import { getNotificationText } from "./notifier.js";
import { SOURCE_TYPES } from "./protocol.js";

const NOTIFICATION_ICON = "icon128.png";
const WEB_SOURCE_TYPE = SOURCE_TYPES.find((value) => value === "web") || "web";
const YOUTUBE_SOURCE_TYPE = SOURCE_TYPES.find((value) => value === "youtube") || "youtube";
const BACKEND_BASE_URL = resolveBackendBaseUrl();

chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "capture-selection") {
    return;
  }
  await captureActiveSelection();
});

chrome.action.onClicked.addListener(async () => {
  await captureActiveSelection();
});

async function captureActiveSelection() {
  if (!BACKEND_BASE_URL) {
    await showNotification(undefined, "扩展未配置本地后端地址");
    return;
  }

  const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!activeTab?.id) {
    await showNotification(undefined, "无法读取当前页面");
    return;
  }

  let payload;
  try {
    payload = await chrome.tabs.sendMessage(activeTab.id, { type: "collect-selection" });
  } catch (error) {
    await showNotification(undefined, String(error));
    return;
  }

  const requestPayload = {
    ...payload,
    source_type: detectSourceType(activeTab.url),
  };
  const response = await captureSelection(BACKEND_BASE_URL, requestPayload);
  await showNotification(response.status, response.message);
}

async function showNotification(status, fallbackMessage) {
  const message = getNotificationText(status, fallbackMessage);
  await chrome.notifications.create({
    type: "basic",
    iconUrl: NOTIFICATION_ICON,
    title: "Sherber Queue Capture",
    message,
  });
}

function detectSourceType(url) {
  if (typeof url === "string" && url.includes("youtube.com")) {
    return YOUTUBE_SOURCE_TYPE;
  }
  return WEB_SOURCE_TYPE;
}

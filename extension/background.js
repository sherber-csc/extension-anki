import { captureSelection, resolveBackendBaseUrl } from "./api-client.js";
import { getNotificationText } from "./notifier.js";
import { SOURCE_TYPES } from "./protocol.js";

const NOTIFICATION_ICON = "icon128.png";
const WEB_SOURCE_TYPE = SOURCE_TYPES.find((value) => value === "web") || "web";
const YOUTUBE_SOURCE_TYPE = SOURCE_TYPES.find((value) => value === "youtube") || "youtube";
const BACKEND_BASE_URL = resolveBackendBaseUrl();
const CAPTURE_CONTEXT_MENU_ID = "capture-selection-context-menu";
const CAPTURE_CONTEXT_MENU_TITLE = "Capture selected word";

registerCaptureContextMenu();
chrome.runtime.onInstalled.addListener(() => {
  registerCaptureContextMenu();
});
chrome.runtime.onStartup.addListener(() => {
  registerCaptureContextMenu();
});

chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "capture-selection") {
    return;
  }
  await captureActiveSelection();
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== CAPTURE_CONTEXT_MENU_ID) {
    return;
  }
  await captureActiveSelection(tab);
});

chrome.action.onClicked.addListener(async () => {
  await captureActiveSelection();
});

async function captureActiveSelection(activeTabOverride) {
  if (!BACKEND_BASE_URL) {
    await showNotification(undefined, "扩展未配置本地后端地址");
    return;
  }

  let activeTab = activeTabOverride;
  if (!activeTab?.id) {
    [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
  }

  if (!activeTab?.id) {
    await showNotification(undefined, "无法读取当前页面");
    return;
  }

  let payload;
  try {
    payload = await chrome.tabs.sendMessage(activeTab.id, { type: "collect-selection" });
  } catch (error) {
    await showNotification(undefined, formatContentScriptError(error));
    return;
  }

  const requestPayload = {
    ...payload,
    source_type: detectSourceType(activeTab.url),
  };

  console.debug("[Sherber][background-capture-debug]", {
    surface_form: requestPayload.surface_form,
    source_sentence: requestPayload.source_sentence,
    source_type: requestPayload.source_type,
    source_url: requestPayload.source_url,
  });

  const response = await captureSelection(BACKEND_BASE_URL, requestPayload);
  await showNotification(response.status, response.message);
}

function registerCaptureContextMenu() {
  chrome.contextMenus.remove(CAPTURE_CONTEXT_MENU_ID, () => {
    void chrome.runtime.lastError;
    chrome.contextMenus.create(
      {
        id: CAPTURE_CONTEXT_MENU_ID,
        title: CAPTURE_CONTEXT_MENU_TITLE,
        contexts: ["selection", "page"],
      },
      () => {
        void chrome.runtime.lastError;
      }
    );
  });
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

function formatContentScriptError(error) {
  const message = error instanceof Error ? error.message : String(error);
  if (message.includes("Receiving end does not exist")) {
    return "当前网页未连接扩展采集脚本，请刷新当前网页后重试。";
  }
  return message;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "collect-selection") {
    return;
  }

  sendResponse(collectSelectionPayload());
});

function collectSelectionPayload() {
  const selection = window.getSelection();
  const surfaceForm = selection?.toString().trim() || "";

  return {
    surface_form: surfaceForm,
    source_sentence: bestEffortSourceSentence(selection),
    source_title: document.title || null,
    source_url: window.location.href || null,
    source_timestamp: bestEffortTimestamp(),
    captured_at: new Date().toISOString(),
  };
}

function bestEffortSourceSentence(selection) {
  if (!selection || selection.rangeCount === 0) {
    return null;
  }

  const selectedText = selection.toString().trim();
  if (!selectedText) {
    return null;
  }

  const anchorNode = selection.getRangeAt(0).commonAncestorContainer;
  const parentElement =
    anchorNode.nodeType === Node.ELEMENT_NODE ? anchorNode : anchorNode.parentElement;
  const rawText = parentElement?.textContent?.replace(/\s+/g, " ").trim();
  if (!rawText) {
    return null;
  }

  const sentences = rawText
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);

  for (const sentence of sentences) {
    if (sentence.includes(selectedText)) {
      return sentence;
    }
  }

  return null;
}

function bestEffortTimestamp() {
  if (!window.location.hostname.includes("youtube.com")) {
    return null;
  }

  const video = document.querySelector("video");
  if (!video || Number.isNaN(video.currentTime)) {
    return null;
  }

  const totalSeconds = Math.floor(video.currentTime);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}

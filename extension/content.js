let lastContextMenuTarget = null;

document.addEventListener(
  "contextmenu",
  (event) => {
    lastContextMenuTarget = event.target instanceof Node ? event.target : null;
  },
  true
);

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "collect-selection") {
    return;
  }

  sendResponse(collectSelectionPayload());
});

function collectSelectionPayload() {
  const selection = window.getSelection();
  const rawSelection = selection?.toString() || "";
  let surfaceForm = selection?.toString().trim() || "";
  let sourceSentence = bestEffortSourceSentence(selection);
  let fallbackSource = "native-selection";

  if (!surfaceForm) {
    const trancyFallback = collectTrancyFallbackPayload();
    if (trancyFallback) {
      surfaceForm = trancyFallback.surface_form;
      sourceSentence = trancyFallback.source_sentence;
      fallbackSource = trancyFallback.fallback_source;
    }
  }

  console.debug("[Sherber][content-selection-debug]", {
    raw_selection: rawSelection,
    surface_form: surfaceForm,
    source_sentence: sourceSentence,
    fallback_source: fallbackSource,
    range_count: selection?.rangeCount ?? 0,
    anchor_node: summarizeAnchorNode(selection),
  });

  return {
    surface_form: surfaceForm,
    source_sentence: sourceSentence,
    source_title: document.title || null,
    source_url: window.location.href || null,
    source_timestamp: bestEffortTimestamp(),
    captured_at: new Date().toISOString(),
  };
}

function collectTrancyFallbackPayload() {
  if (!isTrancyLearningModePage()) {
    return null;
  }

  const contextToken = findTrancyContextTargetToken();
  const highlightedToken = contextToken ? null : findTrancyHighlightedToken();
  const tokenElement = contextToken || highlightedToken;
  const subtitleElement = tokenElement?.closest(".trancy-primary-subtitle.lt-en") || findTrancySubtitleElement();
  const candidateWord = tokenElement?.textContent?.trim() || "";
  const fallbackSource = contextToken
    ? "trancy-learning-mode-target"
    : highlightedToken
      ? "trancy-learning-mode-highlight"
      : "native-selection";

  if (!isAcceptableSingleWordCandidate(candidateWord)) {
    console.debug("[Sherber][trancy-fallback-debug]", {
      subtitle_found: Boolean(subtitleElement),
      context_token_found: Boolean(contextToken),
      highlighted_token_found: Boolean(highlightedToken),
      candidate_word: candidateWord,
      fallback_source: fallbackSource,
    });
    return null;
  }

  const candidateSentence = normalizeInlineText(subtitleElement?.textContent);

  return {
    surface_form: candidateWord,
    source_sentence: candidateSentence || null,
    fallback_source: fallbackSource,
  };
}

function isTrancyLearningModePage() {
  return (
    window.location.hostname.includes("youtube.com") &&
    findTrancySubtitleElement() !== null
  );
}

function findTrancySubtitleElement() {
  const selectors = [
    "#trancy-root .trancy-primary-subtitle.lt-en",
    ".wrapper-theater.active .trancy-primary-subtitle.lt-en",
    ".trancy-subtitle-group .trancy-primary-subtitle.lt-en",
    ".trancy-primary-subtitle.lt-en",
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) {
      return element;
    }
  }

  return null;
}

function findTrancyHighlightedToken() {
  const selectors = [
    "#trancy-root .trancy-primary-subtitle.lt-en .token.highlight",
    ".wrapper-theater.active .trancy-primary-subtitle.lt-en .token.highlight",
    ".trancy-subtitle-group .trancy-primary-subtitle.lt-en .token.highlight",
    ".trancy-primary-subtitle.lt-en .token.highlight",
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) {
      return element;
    }
  }

  return null;
}

function findTrancyContextTargetToken() {
  const targetElement = toElement(lastContextMenuTarget);
  if (!targetElement) {
    return null;
  }

  const tokenElement = targetElement.closest(".token");
  if (!tokenElement) {
    return null;
  }

  const subtitleElement = tokenElement.closest(".trancy-primary-subtitle.lt-en");
  return subtitleElement ? tokenElement : null;
}

function isAcceptableSingleWordCandidate(text) {
  const candidate = text.trim();
  if (!candidate || candidate.includes(" ")) {
    return false;
  }
  return /^[A-Za-z]+(?:['’-][A-Za-z]+)*$/.test(candidate);
}

function normalizeInlineText(text) {
  if (typeof text !== "string") {
    return "";
  }
  return text.replace(/\s+/g, " ").trim();
}

function toElement(node) {
  if (!node) {
    return null;
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    return node;
  }
  return node.parentElement || null;
}

function summarizeAnchorNode(selection) {
  if (!selection || selection.rangeCount === 0) {
    return null;
  }

  const anchorNode = selection.getRangeAt(0).commonAncestorContainer;
  if (!anchorNode) {
    return null;
  }

  const text = anchorNode.textContent?.replace(/\s+/g, " ").trim() || "";
  const preview = text.slice(0, 120);

  return {
    node_type: anchorNode.nodeType,
    node_name: anchorNode.nodeName,
    text_preview: preview,
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

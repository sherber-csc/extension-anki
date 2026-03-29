import { fetchQueue, resolveBackendBaseUrl } from "./api-client.js";

const backendBaseUrl = resolveBackendBaseUrl();
const refreshButton = document.getElementById("refresh-button");
const statusElement = document.getElementById("status");
const pendingListElement = document.getElementById("pending-list");

refreshButton.addEventListener("click", async () => {
  await loadQueue();
});

loadQueue();

async function loadQueue() {
  refreshButton.disabled = true;
  refreshButton.textContent = "Loading...";
  statusElement.textContent = "Loading queue...";
  pendingListElement.textContent = "";

  try {
    const payload = await fetchQueue(backendBaseUrl);
    renderPendingItems(Array.isArray(payload.items) ? payload.items : []);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error.";
    statusElement.textContent = `Failed to load queue: ${message}`;
    pendingListElement.innerHTML = '<div class="empty">No data available.</div>';
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = "Refresh";
  }
}

function renderPendingItems(items) {
  const pendingItems = items.filter((item) => item.status === "pending");
  statusElement.textContent = `${pendingItems.length} pending item(s)`;
  pendingListElement.textContent = "";

  if (pendingItems.length === 0) {
    pendingListElement.innerHTML = '<div class="empty">No pending items.</div>';
    return;
  }

  for (const item of pendingItems) {
    const itemElement = document.createElement("div");
    itemElement.className = "queue-item";

    const titleElement = document.createElement("strong");
    titleElement.textContent = item.surface_form;
    itemElement.appendChild(titleElement);

    itemElement.appendChild(createLine(`lemma: ${item.lemma}`));
    itemElement.appendChild(createLine(`word_key: ${item.word_key}`));
    itemElement.appendChild(createLine(`captured_at: ${item.captured_at}`));

    pendingListElement.appendChild(itemElement);
  }
}

function createLine(text) {
  const line = document.createElement("div");
  line.textContent = text;
  return line;
}

import { deletePendingRecord, fetchQueue, generatePending, resolveBackendBaseUrl } from "./api-client.js";

const backendBaseUrl = resolveBackendBaseUrl();
const refreshButton = document.getElementById("refresh-button");
const generateButton = document.getElementById("generate-button");
const statusElement = document.getElementById("status");
const actionMessageElement = document.getElementById("action-message");
const pendingListElement = document.getElementById("pending-list");

refreshButton.addEventListener("click", async () => {
  await loadQueue();
});

generateButton.addEventListener("click", async () => {
  await handleGeneratePending();
});

loadQueue();

async function loadQueue() {
  refreshButton.disabled = true;
  generateButton.disabled = true;
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
    generateButton.disabled = false;
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

    const headerElement = document.createElement("div");
    headerElement.className = "queue-item-header";

    const titleElement = document.createElement("strong");
    titleElement.className = "queue-item-title";
    titleElement.textContent = item.surface_form;
    headerElement.appendChild(titleElement);

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "delete-button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", async () => {
      await handleDeletePending(item.record_id, deleteButton);
    });
    headerElement.appendChild(deleteButton);

    itemElement.appendChild(headerElement);

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

async function handleDeletePending(recordId, buttonElement) {
  buttonElement.disabled = true;
  buttonElement.textContent = "Deleting...";
  actionMessageElement.textContent = `Deleting pending record ${recordId}...`;

  try {
    const result = await deletePendingRecord(backendBaseUrl, recordId);
    if (result.status === "deleted_pending_item") {
      actionMessageElement.textContent = result.message || `Deleted pending record ${recordId}.`;
      await loadQueue();
      return;
    }

    actionMessageElement.textContent = `Delete failed: ${result.message || result.status}`;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error.";
    actionMessageElement.textContent = `Delete failed: ${message}`;
  } finally {
    buttonElement.disabled = false;
    buttonElement.textContent = "Delete";
  }
}

async function handleGeneratePending() {
  generateButton.disabled = true;
  generateButton.textContent = "Generating...";
  actionMessageElement.textContent = "Generating pending cards...";

  try {
    const result = await generatePending(backendBaseUrl);
    actionMessageElement.textContent =
      `${result.status}: ${result.message} ` +
      `(processed=${result.processed_count}, success=${result.success_count}, failed=${result.failed_count})`;
    await loadQueue();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error.";
    actionMessageElement.textContent = `Generate failed: ${message}`;
  } finally {
    generateButton.disabled = false;
    generateButton.textContent = "Generate pending cards";
  }
}

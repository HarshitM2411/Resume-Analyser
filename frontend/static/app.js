const queryEl = document.getElementById("query");
const sendBtn = document.getElementById("send");
const loadingEl = document.getElementById("loading");
const chatThread = document.getElementById("chat-thread");
const welcomeCard = document.getElementById("welcome-card");
const resumesList = document.getElementById("resumes-list");
const outputList = document.getElementById("output-list");
const resumeSearch = document.getElementById("resume-search");
const connectionDot = document.getElementById("connection-dot");
const connectionLabel = document.getElementById("connection-label");
const connectionModel = document.getElementById("connection-model");
const refreshBtn = document.getElementById("refresh-files");
const newAnalysisBtn = document.getElementById("new-analysis");

let allResumes = [];
let selectedResumePath = null;
let isLoading = false;

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function extType(ext) {
  const e = (ext || "").toLowerCase();
  if (e === ".pdf") return "pdf";
  if (e === ".docx") return "docx";
  return "txt";
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatAssistantText(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
}

function getThreadInner() {
  let inner = chatThread.querySelector(".chat-thread-inner");
  if (!inner) {
    inner = document.createElement("div");
    inner.className = "chat-thread-inner";
    chatThread.appendChild(inner);
  }
  return inner;
}

function hideWelcome() {
  welcomeCard.classList.add("hidden");
}

function appendMessage(role, content, options = {}) {
  hideWelcome();
  const inner = getThreadInner();
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const time = formatTime();

  if (role === "user") {
    row.innerHTML = `
      <div class="message-block">
        <div class="message-bubble">${escapeHtml(content)}</div>
        <div class="message-meta">
          <span class="message-time">${time}</span>
        </div>
      </div>`;
  } else {
    const bubbleClass = options.error ? "message-bubble error" : options.loading ? "message-bubble loading" : "message-bubble";
    const body = options.loading
      ? 'Thinking<span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span>'
      : formatAssistantText(content);

    row.innerHTML = `
      <div class="assistant-avatar" aria-hidden="true">
        <span class="material-symbols-outlined">psychology</span>
      </div>
      <div class="message-block">
        <div class="${bubbleClass}">${body}</div>
        ${
          options.loading
            ? ""
            : `<div class="message-meta">
          <span class="message-time">${time}</span>
          <div class="message-actions">
            <button type="button" class="icon-btn copy-btn" title="Copy" aria-label="Copy response">
              <span class="material-symbols-outlined">content_copy</span>
            </button>
          </div>
        </div>`
        }
      </div>`;

    if (!options.loading) {
      row.querySelector(".copy-btn")?.addEventListener("click", () => {
        navigator.clipboard.writeText(content).catch(() => {});
      });
    }
  }

  inner.appendChild(row);
  chatThread.scrollTop = chatThread.scrollHeight;
  return row;
}

function setLoadingState(loading) {
  isLoading = loading;
  sendBtn.disabled = loading;
  document.querySelectorAll(".example-btn, .chip").forEach((btn) => {
    btn.disabled = loading;
  });
  loadingEl.classList.toggle("hidden", !loading);
}

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (!data.api_key_configured) {
      connectionDot.className = "status-dot error";
      connectionLabel.textContent = "NO API KEY";
      connectionModel.textContent = "Set GROQ_API_KEY in .env";
    } else {
      connectionDot.className = "status-dot connected";
      connectionLabel.textContent = "CONNECTED";
      connectionModel.textContent = data.model || "groq";
    }
  } catch {
    connectionDot.className = "status-dot error";
    connectionLabel.textContent = "OFFLINE";
    connectionModel.textContent = "Run: python web_app.py";
  }
}

function renderFileCards(container, files, { compact = false } = {}) {
  container.innerHTML = "";
  if (!files.length) {
    const empty = document.createElement("li");
    empty.className = "file-empty";
    empty.textContent = compact ? "No output files yet" : "No resumes in folder";
    container.appendChild(empty);
    return;
  }

  for (const f of files) {
    const type = extType(f.extension);
    const li = document.createElement("li");
    li.className = "file-card";
    if (!compact && f.filepath === selectedResumePath) {
      li.classList.add("selected");
    }
    li.title = f.filepath;
    li.innerHTML = `
      <span class="material-symbols-outlined file-card-icon ${type}">description</span>
      <div class="file-card-body">
        <span class="file-card-name">${escapeHtml(f.filename)}</span>
        <span class="file-card-meta">${formatBytes(f.size_bytes)}</span>
      </div>
      <span class="file-card-badge ${type}">${type}</span>`;

    if (!compact) {
      li.addEventListener("click", () => {
        selectedResumePath = f.filepath;
        renderFileCards(container, files);
        queryEl.value = `Summarize ${f.filename}`;
        queryEl.focus();
      });
    }

    container.appendChild(li);
  }
}

function filterResumes() {
  const q = resumeSearch.value.trim().toLowerCase();
  const filtered = q
    ? allResumes.filter((f) => f.filename.toLowerCase().includes(q))
    : allResumes;
  renderFileCards(resumesList, filtered);
}

async function loadFiles() {
  try {
    const [resumesRes, outputRes] = await Promise.all([
      fetch("/api/resumes"),
      fetch("/api/output"),
    ]);
    allResumes = await resumesRes.json();
    const output = await outputRes.json();
    filterResumes();
    renderFileCards(outputList, output, { compact: true });
  } catch {
    resumesList.innerHTML = '<li class="file-empty">Failed to load</li>';
    outputList.innerHTML = '<li class="file-empty">Failed to load</li>';
  }
}

async function sendQuery() {
  const query = queryEl.value.trim();
  if (!query || isLoading) return;

  appendMessage("user", query);
  queryEl.value = "";
  setLoadingState(true);

  const loadingRow = appendMessage("assistant", "", { loading: true });

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    loadingRow.remove();

    if (!res.ok) {
      appendMessage("assistant", data.error || res.statusText, { error: true });
    } else {
      appendMessage("assistant", data.answer || "(empty response)");
      await loadFiles();
    }
  } catch (err) {
    loadingRow.remove();
    appendMessage("assistant", err.message, { error: true });
  } finally {
    setLoadingState(false);
    queryEl.focus();
  }
}

document.querySelectorAll(".example-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    queryEl.value = btn.dataset.query;
    sendQuery();
  });
});

sendBtn.addEventListener("click", sendQuery);
queryEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    sendQuery();
  }
});

resumeSearch.addEventListener("input", filterResumes);
refreshBtn.addEventListener("click", loadFiles);

newAnalysisBtn.addEventListener("click", () => {
  queryEl.value = "";
  queryEl.focus();
  welcomeCard.classList.remove("hidden");
  const inner = chatThread.querySelector(".chat-thread-inner");
  if (inner) inner.remove();
});

checkHealth();
loadFiles();

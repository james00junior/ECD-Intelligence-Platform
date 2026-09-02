"use strict";

const SESSION_KEY = "ecd.organisation";
const HISTORY_PREFIX = "ecd.chat.";

const loginView = document.querySelector("#login-view");
const chatView = document.querySelector("#chat-view");
const orgList = document.querySelector("#org-list");
const loginStatus = document.querySelector("#login-status");
const messages = document.querySelector("#messages");
const emptyState = document.querySelector("#empty-state");
const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const sendButton = document.querySelector("#send-button");
const activeOrgName = document.querySelector("#active-org-name");

let session = null;
let sending = false;

function readJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

function writeJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function historyKey(orgId) {
  return `${HISTORY_PREFIX}${orgId}`;
}

function loadSession() {
  const stored = readJson(SESSION_KEY);
  if (!stored || !Number.isInteger(stored.id) || stored.id < 1) return null;
  return {
    id: stored.id,
    name: stored.name || `Organisation ${stored.id}`,
    country: stored.country || "",
  };
}

function saveSession(org) {
  writeJson(SESSION_KEY, org);
}

function loadHistory(orgId) {
  const stored = readJson(historyKey(orgId));
  return Array.isArray(stored) ? stored : [];
}

function saveHistory(orgId, thread) {
  writeJson(historyKey(orgId), thread);
}

function setLoginStatus(text, tone) {
  loginStatus.textContent = text;
  if (tone) loginStatus.dataset.tone = tone;
  else delete loginStatus.dataset.tone;
}

function showLogin() {
  session = null;
  loginView.hidden = false;
  chatView.hidden = true;
  loadOrganisations();
}

function showChat(org) {
  session = org;
  saveSession(org);
  activeOrgName.textContent = org.name;
  loginView.hidden = true;
  chatView.hidden = false;
  renderThread(loadHistory(org.id));
  question.focus();
}

function logout() {
  localStorage.removeItem(SESSION_KEY);
  showLogin();
}

async function loadOrganisations() {
  orgList.replaceChildren();
  setLoginStatus("Loading organisations…");
  try {
    const response = await fetch("/api/v1/organisations");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const organisations = await response.json();
    if (!Array.isArray(organisations) || organisations.length === 0) {
      setLoginStatus(
        "No organisations found. Seed the database, then refresh.",
        "error"
      );
      return;
    }
    setLoginStatus(`${organisations.length} organisation${organisations.length === 1 ? "" : "s"} available.`);
    organisations.forEach((org) => orgList.appendChild(orgButton(org)));
  } catch {
    setLoginStatus(
      "Could not load organisations. Check that the API and database are running.",
      "error"
    );
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "retry-button";
    retry.textContent = "Try again";
    retry.addEventListener("click", loadOrganisations);
    orgList.appendChild(retry);
  }
}

function orgButton(org) {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "org-card";
  button.setAttribute(
    "aria-label",
    `Continue as ${org.name}${org.country ? `, ${org.country}` : ""}`
  );

  const copy = document.createElement("div");
  const name = document.createElement("strong");
  name.textContent = org.name;
  const meta = document.createElement("span");
  const parts = [org.country, `ID ${org.id}`].filter(Boolean);
  meta.textContent = parts.join(" · ");
  copy.append(name, meta);

  const action = document.createElement("span");
  action.className = "org-action";
  action.textContent = "Continue";

  button.append(copy, action);
  button.addEventListener("click", () => showChat({
    id: org.id,
    name: org.name,
    country: org.country || "",
  }));
  item.appendChild(button);
  return item;
}

function renderThread(thread) {
  messages.replaceChildren();
  thread.forEach((item) => appendMessage(item, false));
  emptyState.hidden = thread.length > 0;
  messages.scrollTop = messages.scrollHeight;
}

function persistMessage(item) {
  if (!session) return;
  const thread = loadHistory(session.id);
  thread.push(item);
  saveHistory(session.id, thread);
  emptyState.hidden = true;
}

function appendMessage(item, persist) {
  const article = document.createElement("article");
  article.className = `message ${item.role}`;
  if (item.pending) article.classList.add("typing");

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = item.role === "assistant" ? "✦" : "You";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (item.error) bubble.classList.add("error");

  if (item.pending) {
    const dots = document.createElement("p");
    dots.className = "typing-dots";
    dots.setAttribute("aria-label", "Researching");
    dots.innerHTML = "<span></span><span></span><span></span>";
    bubble.appendChild(dots);
  } else {
    const body = document.createElement("p");
    body.textContent = item.text;
    bubble.appendChild(body);
    if (item.citations && item.citations.length) {
      bubble.appendChild(citationRow(item.citations));
    }
  }

  article.append(avatar, bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  if (persist && !item.pending) persistMessage(item);
  return article;
}

function citationRow(citations) {
  const row = document.createElement("div");
  row.className = "sources";
  citations.forEach((citation) => {
    const label = `[${citation.reference ?? ""}] ${citation.title || citation.source_type || "Source"}`.trim();
    const tag = document.createElement(citation.uri ? "a" : "span");
    tag.className = "source";
    tag.textContent = label;
    if (citation.uri) {
      tag.href = citation.uri;
      tag.target = "_blank";
      tag.rel = "noreferrer noopener";
    }
    row.appendChild(tag);
  });
  return row;
}

function resizeComposer() {
  question.style.height = "auto";
  question.style.height = `${Math.min(question.scrollHeight, 160)}px`;
}

async function ask(text) {
  const trimmed = text.trim();
  if (!session || !trimmed || sending) return;

  sending = true;
  sendButton.disabled = true;
  question.value = "";
  resizeComposer();
  emptyState.hidden = true;

  appendMessage({ role: "user", text: trimmed }, true);
  const pending = appendMessage({ role: "assistant", pending: true }, false);

  try {
    const response = await fetch("/api/v1/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: trimmed,
        organisation_id: session.id,
      }),
    });
    const data = await response.json().catch(() => ({}));
    pending.remove();

    if (!response.ok) {
      appendMessage({
        role: "assistant",
        error: true,
        text: data.detail || data.error || "The research service returned an error.",
      }, true);
      return;
    }

    if (data.error && !data.answer) {
      appendMessage({ role: "assistant", error: true, text: data.error }, true);
      return;
    }

    appendMessage({
      role: "assistant",
      text: data.answer || "I could not find sufficient evidence for that question.",
      citations: data.citations || [],
    }, true);
  } catch {
    pending.remove();
    appendMessage({
      role: "assistant",
      error: true,
      text: "The research service is temporarily unavailable. Please try again.",
    }, true);
  } finally {
    sending = false;
    sendButton.disabled = false;
    question.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(question.value);
});

question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

question.addEventListener("input", resizeComposer);

document.querySelectorAll(".prompt-card").forEach((button) => {
  button.addEventListener("click", () => ask(button.dataset.question));
});

document.querySelector("#logout").addEventListener("click", logout);
document.querySelector("#switch-org").addEventListener("click", () => {
  localStorage.removeItem(SESSION_KEY);
  showLogin();
});

async function loadPlannerStatus() {
  const label = document.querySelector("#llm-status-value");
  const chip = document.querySelector("#llm-status");
  if (!label || !chip) return;
  try {
    const response = await fetch("/api/v1/models/status");
    if (!response.ok) throw new Error("status");
    const data = await response.json();
    const on = data.query_planner_mode === "llm";
    chip.dataset.mode = on ? "llm" : "rule";
    label.textContent = on
      ? `on · ${data.ollama_model || data.llm_provider}`
      : "off";
  } catch {
    chip.dataset.mode = "rule";
    label.textContent = "unknown";
  }
}

const existing = loadSession();
loadPlannerStatus();
if (existing) showChat(existing);
else showLogin();

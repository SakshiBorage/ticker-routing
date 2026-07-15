const API_BASE_URL = "http://127.0.0.1:8000";
const TICKETS_ENDPOINT = `${API_BASE_URL}/admin/tickets`;
const CLASSIFY_ENDPOINT = `${API_BASE_URL}/tickets/classify/validated`;

const CATEGORY_TEAM_MAP = {
  flight_disruption: "Flight Operations & Rebooking",
  baggage: "Baggage Services",
  reservations_ticketing: "Reservations & Ticketing",
  refunds_compensation: "Refunds & Compensation",
  payments_billing: "Payments & Billing",
  loyalty_program: "Loyalty Program Team",
  account_access: "Account & Identity Support",
  special_assistance: "Accessibility & Special Services",
  discrimination_complaint: "Legal & Compliance",
  fraud_security: "Trust & Security",
  safety_incident: "Safety & Compliance",
  technical_platform: "Platform Engineering",
  feedback_complaints: "Customer Relations",
  general_inquiry: "Customer Support Desk",
};

const PRIORITY_RANK = { High: 3, Medium: 2, Low: 1 };

let tickets = [];
let activeStatusFilter = "all";
let activePriorityFilter = "all";
let searchQuery = "";
let sortMode = "date-desc";
let currentReviewId = null;
let activePage = "tickets";
let activeJiraFilter = "all";

let benchManualTimerHandle = null;
let benchManualStartedAt = null;
let benchManualDone = false;
let benchManualResult = null;
let benchAiDone = false;
let benchAiResult = null;
let benchAiError = null;

// ---------- helpers ----------

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function categoryLabel(key) {
  return key
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

function truncate(text, max) {
  return text.length > max ? text.slice(0, max - 1) + "…" : text;
}

function sortTickets(list) {
  const sorted = [...list];
  switch (sortMode) {
    case "date-asc":
      return sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    case "priority-desc":
      return sorted.sort((a, b) => PRIORITY_RANK[b.priority] - PRIORITY_RANK[a.priority]);
    case "priority-asc":
      return sorted.sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]);
    case "status":
      return sorted.sort((a, b) => Number(a.is_verified) - Number(b.is_verified));
    case "date-desc":
    default:
      return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }
}

// ---------- data loading ----------

async function loadTickets() {
  try {
    const response = await fetch(TICKETS_ENDPOINT);
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    tickets = await response.json();
    renderAll();
  } catch (error) {
    console.error("Failed to load tickets:", error);
    showToast("Could not load tickets from the server.");
  }
}

async function refreshTicket(id) {
  try {
    const response = await fetch(`${TICKETS_ENDPOINT}`);
    if (!response.ok) return;
    const latest = await response.json();
    const updated = latest.find((t) => t.id === id);
    if (!updated) return;

    const index = tickets.findIndex((t) => t.id === id);
    if (index === -1) return;
    tickets[index] = updated;
    renderAll();

    if (updated.jira_status === "created") {
      showToast(`Jira ticket ${updated.jira_ticket_key} created for #${updated.id}.`);
    } else if (updated.jira_status === "failed") {
      showToast(`Jira ticket creation failed for #${updated.id}.`);
    }
  } catch (error) {
    console.error("Failed to refresh ticket:", error);
  }
}

// ---------- rendering ----------

function renderStats() {
  document.getElementById("stat-total").textContent = tickets.length;
  document.getElementById("stat-pending").textContent = tickets.filter((t) => !t.is_verified).length;
  document.getElementById("stat-verified").textContent = tickets.filter((t) => t.is_verified).length;
}

function getFilteredTickets() {
  const filtered = tickets.filter((t) => {
    if (activeStatusFilter === "pending" && t.is_verified) return false;
    if (activeStatusFilter === "verified" && !t.is_verified) return false;
    if (activePriorityFilter !== "all" && t.priority !== activePriorityFilter) return false;
    if (searchQuery) {
      const haystack = `${t.id} ${t.input_ticket} ${t.assigned_team} ${categoryLabel(t.category)}`.toLowerCase();
      if (!haystack.includes(searchQuery.toLowerCase())) return false;
    }
    return true;
  });
  return sortTickets(filtered);
}

function renderTable() {
  const rows = getFilteredTickets();
  const tbody = document.getElementById("ticket-tbody");
  const emptyState = document.getElementById("empty-state");

  if (rows.length === 0) {
    tbody.innerHTML = "";
    emptyState.classList.remove("hidden");
  } else {
    emptyState.classList.add("hidden");
    tbody.innerHTML = rows
      .map(
        (t) => `
        <tr data-id="${t.id}">
          <td class="cell-id">#${t.id}</td>
          <td class="cell-ticket">
            <div class="cell-ticket-text" title="${t.input_ticket.replace(/"/g, "&quot;")}">${truncate(t.input_ticket, 80)}</div>
          </td>
          <td>${categoryLabel(t.category)}</td>
          <td><span class="badge badge-${t.priority}"><span class="badge-dot"></span>${t.priority}</span></td>
          <td class="cell-team">${t.assigned_team}</td>
          <td>
            <span class="badge ${t.is_verified ? "badge-verified" : "badge-pending"}">
              <span class="badge-dot"></span>${t.is_verified ? "Verified" : "Pending"}
            </span>
          </td>
          <td class="cell-date">${formatDate(t.created_at)}</td>
          <td>${
            t.is_verified
              ? `<button class="review-btn" disabled>Verified</button>`
              : `<button class="review-btn" data-id="${t.id}">Review</button>`
          }</td>
        </tr>`
      )
      .join("");
  }

  document.querySelectorAll(".review-btn:not([disabled])").forEach((btn) => {
    btn.addEventListener("click", () => openReviewPanel(Number(btn.dataset.id)));
  });
}

function jiraStatusLabel(status) {
  if (status === "pending") return "Pending";
  if (status === "created") return "Created";
  if (status === "failed") return "Failed";
  return "—";
}

function jiraStatusBadgeClass(status) {
  if (status === "pending") return "badge-pending";
  if (status === "created") return "badge-verified";
  if (status === "failed") return "badge-failed";
  return "badge-pending";
}

function getFilteredJiraTickets() {
  const verifiedOnly = tickets.filter((t) => t.is_verified);
  if (activeJiraFilter === "all") return verifiedOnly;
  return verifiedOnly.filter((t) => (t.jira_status || "pending") === activeJiraFilter);
}

function renderJiraTable() {
  const rows = getFilteredJiraTickets();
  const tbody = document.getElementById("jira-tbody");
  const emptyState = document.getElementById("jira-empty-state");

  const failedCount = tickets.filter((t) => t.jira_status === "failed").length;
  const failedBadge = document.getElementById("jira-failed-count");
  failedBadge.textContent = failedCount;
  failedBadge.classList.toggle("hidden", failedCount === 0);

  if (rows.length === 0) {
    tbody.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  tbody.innerHTML = rows
    .map((t) => {
      const status = t.jira_status || "pending";
      const ticketCell = t.jira_ticket_key
        ? `<a href="${t.jira_ticket_url}" target="_blank" rel="noopener">${t.jira_ticket_key}</a>`
        : "—";
      const retryButton =
        status === "failed" || status === "pending"
          ? `<button class="review-btn" data-retry-id="${t.id}">Retry</button>`
          : `<button class="review-btn" disabled>Retry</button>`;

      return `
        <tr data-id="${t.id}">
          <td class="cell-id">#${t.id}</td>
          <td>${categoryLabel(t.category)}</td>
          <td class="cell-team">${t.assigned_team}</td>
          <td class="cell-date">${formatDate(t.created_at)}</td>
          <td>
            <span class="badge ${jiraStatusBadgeClass(status)}">
              <span class="badge-dot"></span>${jiraStatusLabel(status)}
            </span>
          </td>
          <td>${ticketCell}</td>
          <td>${retryButton}</td>
        </tr>`;
    })
    .join("");

  document.querySelectorAll("[data-retry-id]").forEach((btn) => {
    btn.addEventListener("click", () => retryJiraTicket(Number(btn.dataset.retryId)));
  });
}

async function retryJiraTicket(id) {
  // Placeholder call to a retry endpoint that doesn't exist on the backend
  // yet - wiring it up here so the UI is ready as soon as it's added.
  try {
    const response = await fetch(`${TICKETS_ENDPOINT}/${id}/jira/retry`, { method: "POST" });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    showToast(`Retrying Jira ticket creation for #${id}...`);
    setTimeout(() => refreshTicket(id), 2000);
  } catch (error) {
    console.error("Failed to retry Jira ticket:", error);
    showToast("Retry endpoint isn't available yet.");
  }
}

function switchPage(page) {
  activePage = page;
  document.getElementById("page-tickets").classList.toggle("hidden", page !== "tickets");
  document.getElementById("page-jira").classList.toggle("hidden", page !== "jira");
  document.getElementById("page-benchmark").classList.toggle("hidden", page !== "benchmark");
  document.querySelectorAll(".page-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.page === page);
  });
  if (page === "jira") renderJiraTable();
}

function renderAll() {
  renderStats();
  renderTable();
  renderJiraTable();
}

// ---------- review panel ----------

function populateCategoryOptions(select) {
  select.innerHTML = Object.keys(CATEGORY_TEAM_MAP)
    .map((key) => `<option value="${key}">${categoryLabel(key)}</option>`)
    .join("");
}

function populateTeamOptions(select) {
  const teams = [...new Set(Object.values(CATEGORY_TEAM_MAP))];
  select.innerHTML = teams.map((team) => `<option value="${team}">${team}</option>`).join("");
}

function openReviewPanel(id) {
  const ticket = tickets.find((t) => t.id === id);
  // Verified tickets are locked; there's nothing left to review.
  if (!ticket || ticket.is_verified) return;
  currentReviewId = id;

  document.getElementById("review-id").textContent = `#${ticket.id}`;
  document.getElementById("field-input").value = ticket.input_ticket;

  const categorySelect = document.getElementById("field-category");
  populateCategoryOptions(categorySelect);
  categorySelect.value = ticket.category;

  const teamSelect = document.getElementById("field-team");
  populateTeamOptions(teamSelect);
  teamSelect.value = ticket.assigned_team;

  document.getElementById("field-priority").value = ticket.priority;
  document.getElementById("field-reasoning").value = ticket.reasoning;
  document.getElementById("field-created").textContent = formatDate(ticket.created_at);

  const saveBtn = document.getElementById("btn-save");
  saveBtn.disabled = false;
  saveBtn.textContent = "Verify & Save";

  document.getElementById("review-panel").classList.remove("hidden");
  document.getElementById("overlay").classList.remove("hidden");
}

function closeReviewPanel() {
  currentReviewId = null;
  document.getElementById("review-panel").classList.add("hidden");
  document.getElementById("overlay").classList.add("hidden");
}

async function saveReview() {
  const ticket = tickets.find((t) => t.id === currentReviewId);
  if (!ticket) return;

  const payload = {
    category: document.getElementById("field-category").value,
    priority: document.getElementById("field-priority").value,
    assigned_team: document.getElementById("field-team").value,
    reasoning: document.getElementById("field-reasoning").value.trim(),
    is_verified: true,
  };

  const saveBtn = document.getElementById("btn-save");
  saveBtn.disabled = true;
  saveBtn.textContent = "Saving...";

  try {
    const response = await fetch(`${TICKETS_ENDPOINT}/${ticket.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new Error(errorBody?.detail || `Request failed with status ${response.status}`);
    }

    const updated = await response.json();
    const index = tickets.findIndex((t) => t.id === ticket.id);
    tickets[index] = updated;

    closeReviewPanel();
    renderAll();
    showToast(`Ticket #${updated.id} verified. Creating Jira ticket...`);

    // Jira ticket creation runs in the background on the server, so the
    // PATCH response above never has the result yet. One delayed refetch
    // (not a polling loop) is enough to pick up jira_status/jira_ticket_key
    // once that background task finishes.
    setTimeout(() => refreshTicket(updated.id), 2000);
  } catch (error) {
    console.error("Failed to save ticket:", error);
    showToast(error.message || "Could not save changes.");
    saveBtn.disabled = false;
    saveBtn.textContent = "Verify & Save";
  }
}

// ---------- manual vs AI benchmark ----------

function formatSeconds(ms) {
  return `${(ms / 1000).toFixed(1)}s`;
}

function startBenchmark() {
  const ticketText = document.getElementById("bench-ticket-input").value.trim();
  if (!ticketText) return;

  benchManualDone = false;
  benchManualResult = null;
  benchAiDone = false;
  benchAiResult = null;
  benchAiError = null;

  document.getElementById("bench-start-btn").disabled = true;
  document.getElementById("bench-ticket-input").disabled = true;
  document.getElementById("bench-result").classList.add("hidden");
  document.getElementById("bench-waiting").classList.add("hidden");

  const categorySelect = document.getElementById("bench-category");
  populateCategoryOptions(categorySelect);
  categorySelect.value = "";
  categorySelect.disabled = false;

  const teamSelect = document.getElementById("bench-team");
  populateTeamOptions(teamSelect);
  teamSelect.disabled = false;

  document.getElementById("bench-priority").disabled = false;
  document.getElementById("bench-priority").value = "";

  const reasoningField = document.getElementById("bench-reasoning");
  reasoningField.value = "";
  reasoningField.disabled = false;

  document.getElementById("bench-manual-fields").classList.remove("hidden");
  const submitBtn = document.getElementById("bench-submit-btn");
  submitBtn.disabled = false;
  submitBtn.textContent = "Submit Manual";

  benchManualStartedAt = Date.now();
  const timerEl = document.getElementById("bench-manual-timer");
  timerEl.textContent = "0.0s";
  benchManualTimerHandle = setInterval(() => {
    timerEl.textContent = formatSeconds(Date.now() - benchManualStartedAt);
  }, 100);

  // Fires immediately alongside the manual timer, but its result is held
  // back and never rendered until the manual submission locks in - so the
  // admin's manual answer can't be biased by seeing the AI's answer first.
  const aiStartedAt = Date.now();
  fetch(CLASSIFY_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticket: ticketText, persist: false }),
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw new Error(errorBody?.detail || `Request failed with status ${response.status}`);
      }
      return response.json();
    })
    .then((result) => {
      benchAiResult = result;
      benchAiDone = true;
      benchAiResult.duration_ms = Date.now() - aiStartedAt;
      renderBenchmarkResultIfReady();
    })
    .catch((error) => {
      console.error("AI classification failed:", error);
      benchAiError = error.message || "AI classification failed.";
      benchAiDone = true;
      renderBenchmarkResultIfReady();
    });
}

function submitBenchmarkManual() {
  const category = document.getElementById("bench-category").value;
  const priority = document.getElementById("bench-priority").value;
  const team = document.getElementById("bench-team").value;
  const reasoning = document.getElementById("bench-reasoning").value.trim();

  if (!category || !priority || !team || !reasoning) {
    showToast("Fill in category, priority, team, and reasoning before submitting.");
    return;
  }

  clearInterval(benchManualTimerHandle);
  const manualDurationMs = Date.now() - benchManualStartedAt;
  document.getElementById("bench-manual-timer").textContent = formatSeconds(manualDurationMs);

  benchManualResult = { category, priority, team, reasoning, duration_ms: manualDurationMs };
  benchManualDone = true;

  document.getElementById("bench-category").disabled = true;
  document.getElementById("bench-priority").disabled = true;
  document.getElementById("bench-team").disabled = true;
  document.getElementById("bench-reasoning").disabled = true;
  document.getElementById("bench-submit-btn").disabled = true;

  if (!benchAiDone) {
    document.getElementById("bench-waiting").classList.remove("hidden");
  }
  renderBenchmarkResultIfReady();
}

function priorityBadge(priority) {
  return `<span class="badge badge-${priority}"><span class="badge-dot"></span>${priority}</span>`;
}

function renderBenchmarkResultIfReady() {
  if (!benchManualDone || !benchAiDone) return;

  document.getElementById("bench-waiting").classList.add("hidden");
  document.getElementById("bench-result").classList.remove("hidden");

  document.getElementById("bench-manual-time-out").textContent = formatSeconds(benchManualResult.duration_ms);
  document.getElementById("bench-manual-category-out").textContent = categoryLabel(benchManualResult.category);
  document.getElementById("bench-manual-priority-out").innerHTML = priorityBadge(benchManualResult.priority);
  document.getElementById("bench-manual-team-out").textContent = benchManualResult.team;
  document.getElementById("bench-manual-reasoning-out").textContent = benchManualResult.reasoning;

  if (benchAiError) {
    document.getElementById("bench-ai-time-out").textContent = "—";
    document.getElementById("bench-ai-category-out").textContent = benchAiError;
    document.getElementById("bench-ai-priority-out").textContent = "—";
    document.getElementById("bench-ai-team-out").textContent = "—";
    document.getElementById("bench-ai-reasoning-out").textContent = "—";
    document.getElementById("bench-diff-summary").textContent = "AI classification failed for this run.";
    return;
  }

  document.getElementById("bench-ai-time-out").textContent = formatSeconds(benchAiResult.duration_ms);
  document.getElementById("bench-ai-category-out").textContent = categoryLabel(benchAiResult.category);
  document.getElementById("bench-ai-priority-out").innerHTML = priorityBadge(benchAiResult.priority);
  document.getElementById("bench-ai-team-out").textContent = benchAiResult.assigned_team;
  document.getElementById("bench-ai-reasoning-out").textContent = benchAiResult.reasoning;

  const diffMs = benchManualResult.duration_ms - benchAiResult.duration_ms;
  const agree = benchManualResult.category === benchAiResult.category && benchManualResult.priority === benchAiResult.priority;
  const faster = diffMs >= 0 ? "AI" : "Manual";
  const diffText = formatSeconds(Math.abs(diffMs));
  document.getElementById("bench-diff-summary").textContent =
    `${faster} was ${diffText} faster. Category/priority ${agree ? "matched" : "did not match"}.`;
}

function resetBenchmark() {
  document.getElementById("bench-ticket-input").value = "";
  document.getElementById("bench-ticket-input").disabled = false;
  document.getElementById("bench-start-btn").disabled = false;
  document.getElementById("bench-manual-fields").classList.add("hidden");
  document.getElementById("bench-waiting").classList.add("hidden");
  document.getElementById("bench-result").classList.add("hidden");
  document.getElementById("bench-manual-timer").textContent = "0.0s";
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => toast.classList.add("hidden"), 2800);
}

// ---------- event wiring ----------

document.getElementById("filter-tabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-tab");
  if (!btn) return;
  document.querySelectorAll(".filter-tab").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  activeStatusFilter = btn.dataset.filter;
  renderTable();
});

document.getElementById("priority-select").addEventListener("change", (e) => {
  activePriorityFilter = e.target.value;
  renderTable();
});

document.getElementById("sort-select").addEventListener("change", (e) => {
  sortMode = e.target.value;
  renderTable();
});

document.getElementById("search-input").addEventListener("input", (e) => {
  searchQuery = e.target.value;
  renderTable();
});

const HEADER_SORT_CYCLE = {
  id: ["date-desc", "date-asc"],
  category: ["date-desc"],
  priority: ["priority-desc", "priority-asc"],
  status: ["status", "date-desc"],
  date: ["date-desc", "date-asc"],
};

document.querySelectorAll("th.sortable").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.sort;
    const cycle = HEADER_SORT_CYCLE[key] || ["date-desc"];
    const currentIndex = cycle.indexOf(sortMode);
    sortMode = cycle[(currentIndex + 1) % cycle.length];
    document.getElementById("sort-select").value = sortMode;
    renderTable();
  });
});

document.getElementById("field-category").addEventListener("change", (e) => {
  const team = CATEGORY_TEAM_MAP[e.target.value];
  if (team) {
    document.getElementById("field-team").value = team;
  }
});

document.getElementById("page-tabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".page-tab");
  if (!btn) return;
  switchPage(btn.dataset.page);
});

document.getElementById("jira-filter-tabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-tab");
  if (!btn) return;
  document.querySelectorAll("#jira-filter-tabs .filter-tab").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  activeJiraFilter = btn.dataset.jiraFilter;
  renderJiraTable();
});

document.getElementById("bench-category").addEventListener("change", (e) => {
  const team = CATEGORY_TEAM_MAP[e.target.value];
  if (team) {
    document.getElementById("bench-team").value = team;
  }
});

document.getElementById("bench-start-btn").addEventListener("click", startBenchmark);
document.getElementById("bench-submit-btn").addEventListener("click", submitBenchmarkManual);
document.getElementById("bench-reset-btn").addEventListener("click", resetBenchmark);

document.getElementById("panel-close").addEventListener("click", closeReviewPanel);
document.getElementById("btn-cancel").addEventListener("click", closeReviewPanel);
document.getElementById("overlay").addEventListener("click", closeReviewPanel);
document.getElementById("btn-save").addEventListener("click", saveReview);

loadTickets();

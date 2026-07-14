const API_BASE_URL = "http://127.0.0.1:8000";
const TICKETS_ENDPOINT = `${API_BASE_URL}/admin/tickets`;

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

function renderAll() {
  renderStats();
  renderTable();
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
    showToast(`Ticket #${updated.id} verified.`);
  } catch (error) {
    console.error("Failed to save ticket:", error);
    showToast(error.message || "Could not save changes.");
    saveBtn.disabled = false;
    saveBtn.textContent = "Verify & Save";
  }
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

document.getElementById("panel-close").addEventListener("click", closeReviewPanel);
document.getElementById("btn-cancel").addEventListener("click", closeReviewPanel);
document.getElementById("overlay").addEventListener("click", closeReviewPanel);
document.getElementById("btn-save").addEventListener("click", saveReview);

loadTickets();

// Specialist Portal Controller

let currentUser = null;
let activeTicketId = null;

document.addEventListener("DOMContentLoaded", async () => {
    currentUser = await checkAuth("specialist");
    if (!currentUser) return;

    loadTickets();
    loadKnowledge();

    const deptFilter = document.getElementById("deptFilter");
    const statusFilter = document.getElementById("statusFilter");
    if (deptFilter) deptFilter.addEventListener("change", loadTickets);
    if (statusFilter) statusFilter.addEventListener("change", loadTickets);

    const replyForm = document.getElementById("replyForm");
    if (replyForm) replyForm.addEventListener("submit", handleReplySubmit);

    const knowledgeForm = document.getElementById("knowledgeForm");
    if (knowledgeForm) knowledgeForm.addEventListener("submit", handleKnowledgeSubmit);
});

async function loadTickets() {
    const tbody = document.getElementById("specialistTicketsBody");
    if (!tbody) return;

    const dept = document.getElementById("deptFilter") ? document.getElementById("deptFilter").value : "All";
    const status = document.getElementById("statusFilter") ? document.getElementById("statusFilter").value : "all";

    try {
        const res = await fetch(`/tickets?department=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}`, {
            credentials: "include"
        });
        const tickets = await res.json();

        if (!tickets || tickets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 30px;">No tickets match current filters.</td></tr>`;
            return;
        }

        tbody.innerHTML = tickets.map(t => `
            <tr>
                <td><strong>${t.ticket_id}</strong></td>
                <td>
                    <div>${escapeHtml(t.question)}</div>
                    <div style="font-size: 11px; color: var(--text-dim);">By: ${t.employee_name || 'Employee'} (${t.employee_email || '-'})</div>
                </td>
                <td><span class="badge-priority ${(t.priority || 'medium').toLowerCase()}">${t.priority || 'Medium'}</span></td>
                <td>${t.department}</td>
                <td><span class="badge-status ${(t.status || 'open').toLowerCase()}">${t.status}</span></td>
                <td>
                    <div style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; color: #94a3b8;">
                        ${t.latest_reply ? escapeHtml(t.latest_reply) : '<em>No reply yet</em>'}
                    </div>
                </td>
                <td>
                    <button class="btn btn-primary" style="padding: 5px 12px; font-size: 12px;" onclick="openReplyModal('${t.ticket_id}', '${escapeHtml(t.question)}')">Respond</button>
                </td>
            </tr>
        `).join("");

    } catch (err) {
        console.error("Failed to load specialist tickets:", err);
    }
}

function openReplyModal(ticketId, question) {
    activeTicketId = ticketId;
    document.getElementById("modalTicketId").textContent = ticketId;
    document.getElementById("modalQuestion").textContent = question;
    document.getElementById("replyText").value = "";
    document.getElementById("replyModal").classList.add("active");
}

function closeReplyModal() {
    document.getElementById("replyModal").classList.remove("active");
    activeTicketId = null;
}

async function handleReplySubmit(e) {
    e.preventDefault();
    if (!activeTicketId) return;

    const reply = document.getElementById("replyText").value.trim();
    const status = document.getElementById("replyStatus").value;

    if (!reply) return;

    try {
        const res = await fetch(`/tickets/${activeTicketId}/reply`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ reply, status })
        });

        if (res.ok) {
            closeReplyModal();
            loadTickets();
        } else {
            const err = await res.json();
            alert(err.detail || "Failed to submit reply.");
        }
    } catch (err) {
        alert("Network error.");
    }
}

// Knowledge Base Management
async function loadKnowledge() {
    const tbody = document.getElementById("knowledgeBody");
    if (!tbody) return;

    try {
        const res = await fetch("/specialist/knowledge", { credentials: "include" });
        const items = await res.json();

        if (!items || items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color: var(--text-dim); padding: 20px;">No custom knowledge articles published yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = items.map(k => `
            <tr>
                <td><strong>${escapeHtml(k.title)}</strong></td>
                <td><span class="badge-priority medium">${k.category}</span></td>
                <td style="font-size: 12px;">${escapeHtml(k.content)}</td>
                <td>
                    <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="deleteKnowledge(${k.id})">Delete</button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Knowledge load error:", err);
    }
}

async function handleKnowledgeSubmit(e) {
    e.preventDefault();
    const title = document.getElementById("kTitle").value.trim();
    const category = document.getElementById("kCategory").value;
    const content = document.getElementById("kContent").value.trim();

    if (!title || !content) return;

    try {
        const res = await fetch("/specialist/knowledge", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ category, title, content })
        });

        if (res.ok) {
            document.getElementById("kTitle").value = "";
            document.getElementById("kContent").value = "";
            loadKnowledge();
            alert("Knowledge article published to AI knowledge base!");
        }
    } catch (err) {
        alert("Error publishing knowledge article.");
    }
}

async function deleteKnowledge(id) {
    if (!confirm("Are you sure you want to remove this knowledge article?")) return;
    try {
        const res = await fetch(`/specialist/knowledge/${id}`, {
            method: "DELETE",
            credentials: "include"
        });
        if (res.ok) loadKnowledge();
    } catch (err) {
        alert("Failed to delete.");
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

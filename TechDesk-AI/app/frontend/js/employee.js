// Employee Dashboard Controller

let currentUser = null;

document.addEventListener("DOMContentLoaded", async () => {
    currentUser = await checkAuth("employee");
    if (!currentUser) return;

    loadTickets();
    loadNotifications();

    const askForm = document.getElementById("askForm");
    if (askForm) {
        askForm.addEventListener("submit", handleAsk);
    }
});

async function handleAsk(e) {
    e.preventDefault();
    const input = document.getElementById("askInput");
    const question = input.value.trim();
    if (!question) return;

    // Append user message
    appendMessage(question, "user");
    input.value = "";

    // Show typing bubble
    const typingId = appendMessage("TechDesk AI agent analyzing inquiry...", "bot", true);

    try {
        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ question })
        });

        const data = await res.json();
        removeMessage(typingId);

        if (!res.ok) {
            appendMessage(data.detail || "Error processing request.", "bot");
            return;
        }

        let bubbleClass = "bot";
        let extraInfo = "";

        if (data.status === "ticket_created") {
            bubbleClass = "ticket";
            extraInfo = `<br><br><span class="badge-priority ${data.priority.toLowerCase()}">${data.priority} Priority</span> &bull; Routed to: <strong>${data.department}</strong>`;
            loadTickets(); // Refresh ticket list
            loadNotifications();
        }

        appendMessage(data.answer + extraInfo, bubbleClass);

    } catch (err) {
        removeMessage(typingId);
        appendMessage("Network error communicating with AI agent.", "bot");
    }
}

function appendMessage(text, type, isTyping = false) {
    const box = document.getElementById("chatMessages");
    const div = document.createElement("div");
    const msgId = "msg_" + Date.now() + Math.random().toString(36).substr(2, 4);
    div.id = msgId;
    div.className = `chat-bubble ${type}`;
    div.innerHTML = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return msgId;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

async function loadTickets() {
    const tbody = document.getElementById("ticketsBody");
    if (!tbody) return;

    try {
        const res = await fetch("/tickets", { credentials: "include" });
        const tickets = await res.json();

        if (!tickets || tickets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-dim); padding: 30px;">No support tickets yet. Inquire with the AI assistant or log a ticket.</td></tr>`;
            return;
        }

        tbody.innerHTML = tickets.map(t => `
            <tr>
                <td><strong>${t.ticket_id}</strong></td>
                <td>${escapeHtml(t.question)}</td>
                <td><span class="badge-priority ${(t.priority || 'medium').toLowerCase()}">${t.priority || 'Medium'}</span></td>
                <td>${t.department || 'IT Helpdesk'}</td>
                <td><span class="badge-status ${(t.status || 'open').toLowerCase()}">${t.status || 'open'}</span></td>
                <td>
                    ${t.status === 'resolved' && !t.rating ?
                        `<button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="openRateModal('${t.ticket_id}')">⭐ Rate</button>` :
                        (t.rating ? `<span>⭐ ${t.rating}/5</span>` : `<button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="viewDetails('${t.ticket_id}')">View</button>`)
                    }
                </td>
            </tr>
        `).join("");

    } catch (err) {
        console.error("Failed to load tickets:", err);
    }
}

async function loadNotifications() {
    const list = document.getElementById("notifList");
    const countBadge = document.getElementById("notifCount");
    if (!list) return;

    try {
        const res = await fetch("/notifications", { credentials: "include" });
        const notifs = await res.json();

        const unread = notifs.filter(n => !n.is_read).length;
        if (countBadge) {
            countBadge.textContent = unread;
            countBadge.style.display = unread > 0 ? "inline-block" : "none";
        }

        if (notifs.length === 0) {
            list.innerHTML = `<div style="padding: 12px; color: var(--text-dim); font-size: 12px;">No notifications.</div>`;
            return;
        }

        list.innerHTML = notifs.map(n => `
            <div style="padding: 10px; border-bottom: 1px solid var(--border); font-size: 12px;">
                <div style="color: var(--text-main);">${escapeHtml(n.message)}</div>
                <div style="color: var(--text-dim); font-size: 10px; margin-top: 4px;">${n.created_at}</div>
            </div>
        `).join("");

    } catch (err) {
        console.error("Notifications error:", err);
    }
}

// Modal handling
let currentRateTicketId = null;

function openRateModal(ticketId) {
    currentRateTicketId = ticketId;
    document.getElementById("rateTicketIdText").textContent = ticketId;
    document.getElementById("rateModal").classList.add("active");
}

function closeRateModal() {
    document.getElementById("rateModal").classList.remove("active");
}

async function submitRating(stars) {
    if (!currentRateTicketId) return;
    try {
        const res = await fetch(`/tickets/${currentRateTicketId}/rate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ rating: stars })
        });
        if (res.ok) {
            closeRateModal();
            loadTickets();
        }
    } catch (err) {
        alert("Failed to submit rating.");
    }
}

async function viewDetails(ticketId) {
    try {
        const res = await fetch(`/tickets/${ticketId}`, { credentials: "include" });
        const data = await res.json();
        const t = data.ticket;
        const replies = data.replies || [];

        let html = `<strong>Ticket:</strong> ${t.ticket_id}<br>`;
        html += `<strong>Department:</strong> ${t.department} | <strong>Priority:</strong> ${t.priority}<br>`;
        html += `<strong>Issue:</strong> ${escapeHtml(t.question)}<br><br>`;

        if (replies.length > 0) {
            html += `<strong>Specialist Replies:</strong><div style="margin-top: 8px; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">`;
            replies.forEach(r => {
                html += `<p style="margin-bottom: 6px;"><strong>${r.specialist_name || 'Specialist'}:</strong> ${escapeHtml(r.reply)} <span style="font-size:10px; color:gray;">(${r.created_at})</span></p>`;
            });
            html += `</div>`;
        } else {
            html += `<em>No specialist replies yet. Ticket is currently in queue.</em>`;
        }

        document.getElementById("detailModalContent").innerHTML = html;
        document.getElementById("detailModal").classList.add("active");
    } catch (err) {
        alert("Failed to load ticket details.");
    }
}

function closeDetailModal() {
    document.getElementById("detailModal").classList.remove("active");
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

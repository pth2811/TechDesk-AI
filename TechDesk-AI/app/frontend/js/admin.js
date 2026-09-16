// Admin Operations Controller

let currentUser = null;

document.addEventListener("DOMContentLoaded", async () => {
    currentUser = await checkAuth("admin");
    if (!currentUser) return;

    loadStats();
    loadAllTickets();
    loadAllUsers();
});

async function loadStats() {
    try {
        const res = await fetch("/admin/stats", { credentials: "include" });
        const data = await res.json();

        document.getElementById("statTotalTickets").textContent = data.total_tickets || 0;
        document.getElementById("statResolvedTickets").textContent = data.resolved_tickets || 0;
        document.getElementById("statCriticalTickets").textContent = (data.priority_distribution && data.priority_distribution.Critical) || 0;
        document.getElementById("statTotalUsers").textContent = data.total_users || 0;
        document.getElementById("statTotalChats").textContent = data.total_chats || 0;
        document.getElementById("statArticles").textContent = data.knowledge_articles || 0;
    } catch (err) {
        console.error("Stats load error:", err);
    }
}

async function loadAllTickets() {
    const tbody = document.getElementById("adminTicketsBody");
    if (!tbody) return;

    try {
        const res = await fetch("/tickets?status=all&department=All", { credentials: "include" });
        const tickets = await res.json();

        if (!tickets || tickets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 30px;">No tickets recorded in system.</td></tr>`;
            return;
        }

        tbody.innerHTML = tickets.map(t => `
            <tr>
                <td><strong>${t.ticket_id}</strong></td>
                <td>
                    <div>${escapeHtml(t.question)}</div>
                    <div style="font-size: 11px; color: var(--text-dim);">By: ${t.employee_name || 'User'} (${t.employee_email || '-'})</div>
                </td>
                <td><span class="badge-priority ${(t.priority || 'medium').toLowerCase()}">${t.priority || 'Medium'}</span></td>
                <td>${t.department}</td>
                <td><span class="badge-status ${(t.status || 'open').toLowerCase()}">${t.status}</span></td>
                <td style="font-size: 12px;">
                    ${t.latest_reply ?
                        `<div>${escapeHtml(t.latest_reply)}</div><div style="font-size:10px; color:gray;">By: ${t.specialist_name || 'Specialist'}</div>` :
                        '<em>Pending reply</em>'
                    }
                </td>
                <td>
                    ${t.latest_reply ?
                        `<button class="btn btn-success" style="padding: 4px 8px; font-size: 11px;" onclick="approveReply('${t.ticket_id}')">Approve as KB Article</button>` :
                        '-'
                    }
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Failed to load admin tickets:", err);
    }
}

async function approveReply(ticketId) {
    if (!confirm(`Promote the resolution of ticket ${ticketId} to the permanent Enterprise Knowledge Base?`)) return;

    try {
        const res = await fetch("/admin/approve-reply", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ ticket_id: ticketId })
        });

        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            loadStats();
        } else {
            alert(data.detail || "Approval failed.");
        }
    } catch (err) {
        alert("Network error.");
    }
}

async function loadAllUsers() {
    const tbody = document.getElementById("adminUsersBody");
    if (!tbody) return;

    try {
        const res = await fetch("/admin/users", { credentials: "include" });
        const users = await res.json();

        tbody.innerHTML = users.map(u => `
            <tr>
                <td><strong>${u.id}</strong></td>
                <td>${escapeHtml(u.name)}</td>
                <td>${escapeHtml(u.email)}</td>
                <td><span class="role-tag">${u.role}</span></td>
                <td>${u.department || 'General'}</td>
                <td>${u.created_at || '-'}</td>
                <td>
                    ${u.id !== currentUser.id ?
                        `<button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="deleteUserAccount(${u.id})">Delete</button>` :
                        '<span style="font-size: 11px; color: var(--text-dim);">Current Admin</span>'
                    }
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Failed to load users:", err);
    }
}

async function deleteUserAccount(userId) {
    if (!confirm("Are you sure you want to delete this user account?")) return;
    try {
        const res = await fetch(`/admin/users/${userId}`, {
            method: "DELETE",
            credentials: "include"
        });
        if (res.ok) {
            loadAllUsers();
            loadStats();
        } else {
            const err = await res.json();
            alert(err.detail || "Failed to delete user.");
        }
    } catch (err) {
        alert("Network error.");
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

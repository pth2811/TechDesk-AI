// Authentication Helper for TechDesk AI

async function checkAuth(requiredRole = null) {
    try {
        const res = await fetch("/auth/me", { credentials: "include" });
        if (!res.ok) {
            window.location.replace("/");
            return null;
        }
        const data = await res.json();
        const user = data.user;

        if (requiredRole && user.role.toLowerCase() !== requiredRole.toLowerCase() && user.role.toLowerCase() !== "admin") {
            alert("Access restricted for your account role.");
            window.location.replace(data.dashboard);
            return null;
        }

        // Populate user info if elements exist
        const nameEl = document.getElementById("userName");
        const roleEl = document.getElementById("userRole");
        const deptEl = document.getElementById("userDept");

        if (nameEl) nameEl.textContent = user.name;
        if (roleEl) roleEl.textContent = user.role.toUpperCase();
        if (deptEl) deptEl.textContent = user.department || "General";

        return user;
    } catch (err) {
        console.error("Auth verification failed:", err);
        window.location.replace("/");
        return null;
    }
}

async function logout() {
    try {
        await fetch("/auth/logout", {
            method: "POST",
            credentials: "include"
        });
    } finally {
        window.location.replace("/");
    }
}

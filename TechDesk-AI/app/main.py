import os
from pathlib import Path
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.database.database import (
    create_tables,
    save_user,
    get_users,
    get_user,
    get_user_by_email,
    get_login_user_by_email,
    delete_user,
    save_ticket,
    get_tickets,
    get_ticket,
    update_ticket_status,
    rate_ticket,
    save_ticket_reply,
    get_ticket_replies,
    approve_latest_ticket_reply,
    save_chat,
    get_chat_history,
    save_notification,
    get_notifications,
    mark_notifications_read,
    save_it_knowledge,
    get_it_knowledge,
    update_it_knowledge,
    delete_it_knowledge
)
from app.auth import (
    create_login_session,
    logout_session,
    get_current_user,
    require_roles,
    hash_password,
    verify_password,
    get_role_dashboard,
    SPECIALIST_ACCESS_CODE,
    ADMIN_ACCESS_CODE
)
from app.agent import run_agent
from app.email_service import send_ticket_created_email, send_ticket_status_email
from app.password_reset import router as password_reset_router

# Initialize database tables
create_tables()

# =========================================================
# APP INITIALIZATION
# =========================================================

app = FastAPI(
    title="TechDesk AI",
    description="Enterprise IT Help Desk & Autonomous Multi-Agent Service Portal",
    version="1.0.0"
)

app.include_router(password_reset_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

APP_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = APP_DIR / "frontend"


# =========================================================
# REQUEST DATA MODELS
# =========================================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "employee"
    department: str = "General"
    access_code: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AskRequest(BaseModel):
    question: str


class ManualTicketRequest(BaseModel):
    question: str
    intent: str = "general"
    department: str = "General IT Helpdesk"
    priority: str = "Medium"


class TicketReplyRequest(BaseModel):
    reply: str
    status: str = "resolved"


class TicketStatusRequest(BaseModel):
    status: str


class TicketRateRequest(BaseModel):
    rating: int


class KnowledgeRequest(BaseModel):
    category: str
    title: str
    content: str


class ApproveReplyRequest(BaseModel):
    ticket_id: str


# =========================================================
# FRONTEND STATIC ROUTES
# =========================================================

@app.get("/", include_in_schema=False)
def index_page():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/register", include_in_schema=False)
def register_page():
    return FileResponse(FRONTEND_DIR / "register.html")


@app.get("/employee-dashboard", include_in_schema=False)
def employee_dashboard(current_user=Depends(require_roles("employee", "specialist", "admin"))):
    return FileResponse(FRONTEND_DIR / "employee.html")


@app.get("/specialist-dashboard", include_in_schema=False)
def specialist_dashboard(current_user=Depends(require_roles("specialist", "admin"))):
    return FileResponse(FRONTEND_DIR / "specialist.html")


@app.get("/admin-dashboard", include_in_schema=False)
def admin_dashboard(current_user=Depends(require_roles("admin"))):
    return FileResponse(FRONTEND_DIR / "admin.html")


@app.get("/password-reset.html", include_in_schema=False)
def password_reset_page():
    return FileResponse(FRONTEND_DIR / "password-reset.html")


@app.get("/forgot-password", include_in_schema=False)
def forgot_password_page():
    return FileResponse(FRONTEND_DIR / "password-reset.html")


@app.get("/css/{filename}", include_in_schema=False)
def serve_css(filename: str):
    css_file = FRONTEND_DIR / "css" / filename
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")


@app.get("/js/{filename}", include_in_schema=False)
def serve_js(filename: str):
    js_file = FRONTEND_DIR / "js" / filename
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript file not found")


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "app": "TechDesk AI",
        "version": "1.0.0",
        "service": "operational"
    }


# =========================================================
# AUTHENTICATION ENDPOINTS
# =========================================================

@app.post("/auth/register")
def register(req: RegisterRequest, response: Response):
    email = req.email.strip().lower()
    name = req.name.strip()
    role = req.role.strip().lower()
    department = req.department.strip() or "General"

    if role not in ["employee", "specialist", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    # Validate access codes for privileged roles
    if role == "specialist" and req.access_code.strip() != SPECIALIST_ACCESS_CODE:
        raise HTTPException(status_code=403, detail="Invalid Specialist Access Code. Contact IT Ops.")

    if role == "admin" and req.access_code.strip() != ADMIN_ACCESS_CODE:
        raise HTTPException(status_code=403, detail="Invalid Admin Security Code.")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    password_hash = hash_password(req.password)
    user_id = save_user(name, email, password_hash, role=role, department=department)

    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to create user account.")

    create_login_session(response, user_id)
    return {
        "message": "Account created successfully.",
        "role": role,
        "dashboard": get_role_dashboard(role)
    }


@app.post("/auth/login")
def login(req: LoginRequest, response: Response):
    email = req.email.strip().lower()
    user = get_login_user_by_email(email)

    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Incorrect email address or password.")

    create_login_session(response, user["id"])
    role = user.get("role", "employee")

    return {
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": role,
            "department": user.get("department", "General")
        },
        "dashboard": get_role_dashboard(role)
    }


@app.get("/auth/me")
def me(current_user=Depends(require_roles("employee", "specialist", "admin"))):
    return {
        "user": current_user,
        "dashboard": get_role_dashboard(current_user.get("role"))
    }


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    logout_session(request, response)
    return {"message": "Logged out successfully."}


# =========================================================
# AI QUERY & TICKETING AGENT
# =========================================================

@app.post("/ask")
def ask(
    req: AskRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_roles("employee", "specialist", "admin"))
):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Inquiry cannot be empty.")

    result = run_agent(question, user_id=current_user["id"])

    # Log in chat table
    try:
        save_chat(
            question=question,
            answer=result["answer"],
            intent=result.get("intent", "general"),
            priority=result.get("priority", "Medium"),
            agent_type=result.get("status", "general"),
            user_id=current_user["id"]
        )
    except Exception as e:
        print(f"Chat save error: {e}")

    # If ticket was created, dispatch email notification in background
    ticket_id = result.get("ticket_id")
    if ticket_id and current_user.get("email"):
        background_tasks.add_task(
            send_ticket_created_email,
            to_email=current_user["email"],
            ticket_id=ticket_id,
            question=question,
            department=result.get("department", "General IT Helpdesk"),
            priority=result.get("priority", "Medium")
        )

        save_notification(
            user_id=current_user["id"],
            ticket_id=ticket_id,
            message=f"Support ticket {ticket_id} ({result.get('priority')} Priority) has been created."
        )

    return result


# =========================================================
# TICKET MANAGEMENT ENDPOINTS
# =========================================================

@app.get("/tickets")
def list_tickets(
    status: str = "all",
    department: str = "All",
    current_user=Depends(require_roles("employee", "specialist", "admin"))
):
    role = current_user.get("role", "employee").lower()

    if role == "employee":
        # Employees only see their own tickets
        return get_tickets(user_id=current_user["id"], status_filter=status)
    else:
        # Specialists and Admins can see all tickets or filter by department
        dept = None if department == "All" else department
        return get_tickets(department=dept, status_filter=status)


@app.get("/tickets/{ticket_id}")
def view_ticket(
    ticket_id: str,
    current_user=Depends(require_roles("employee", "specialist", "admin"))
):
    tkt = get_ticket(ticket_id)
    if not tkt:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    # Employees can only access their own tickets
    if current_user["role"] == "employee" and tkt.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied to this ticket.")

    replies = get_ticket_replies(ticket_id)
    return {
        "ticket": tkt,
        "replies": replies
    }


@app.post("/tickets/create")
def manual_create_ticket(
    req: ManualTicketRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_roles("employee", "specialist", "admin"))
):
    ticket_id = save_ticket(
        question=req.question.strip(),
        intent=req.intent,
        department=req.department,
        priority=req.priority,
        user_id=current_user["id"]
    )

    if current_user.get("email"):
        background_tasks.add_task(
            send_ticket_created_email,
            to_email=current_user["email"],
            ticket_id=ticket_id,
            question=req.question,
            department=req.department,
            priority=req.priority
        )

    save_notification(
        user_id=current_user["id"],
        ticket_id=ticket_id,
        message=f"Manual ticket {ticket_id} submitted to {req.department}."
    )

    return {
        "message": "Ticket created successfully.",
        "ticket_id": ticket_id
    }


@app.post("/tickets/{ticket_id}/reply")
def reply_ticket(
    ticket_id: str,
    req: TicketReplyRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_roles("specialist", "admin"))
):
    tkt = get_ticket(ticket_id)
    if not tkt:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    reply_id = save_ticket_reply(
        ticket_id=ticket_id,
        reply=req.reply.strip(),
        specialist_user_id=current_user["id"]
    )

    # Update status (e.g. resolved or in_progress)
    update_ticket_status(ticket_id, req.status)

    # Notify ticket owner
    if tkt.get("user_id"):
        save_notification(
            user_id=tkt["user_id"],
            ticket_id=ticket_id,
            message=f"IT Specialist {current_user['name']} replied to your ticket {ticket_id}."
        )

        if tkt.get("employee_email"):
            background_tasks.add_task(
                send_ticket_status_email,
                to_email=tkt["employee_email"],
                ticket_id=ticket_id,
                new_status=req.status,
                reply_text=req.reply
            )

    return {
        "message": "Reply sent successfully.",
        "reply_id": reply_id,
        "status": req.status
    }


@app.post("/tickets/{ticket_id}/status")
def change_status(
    ticket_id: str,
    req: TicketStatusRequest,
    current_user=Depends(require_roles("specialist", "admin"))
):
    tkt = get_ticket(ticket_id)
    if not tkt:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    update_ticket_status(ticket_id, req.status)

    if tkt.get("user_id"):
        save_notification(
            user_id=tkt["user_id"],
            ticket_id=ticket_id,
            message=f"Ticket {ticket_id} status updated to {req.status}."
        )

    return {"message": f"Ticket status changed to {req.status}."}


@app.post("/tickets/{ticket_id}/rate")
def rate(
    ticket_id: str,
    req: TicketRateRequest,
    current_user=Depends(require_roles("employee"))
):
    tkt = get_ticket(ticket_id)
    if not tkt:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if tkt.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only rate your own tickets.")

    rate_ticket(ticket_id, req.rating)
    return {"message": "Thank you for your feedback rating!"}


# =========================================================
# NOTIFICATIONS ENDPOINTS
# =========================================================

@app.get("/notifications")
def get_user_notifications(current_user=Depends(require_roles("employee", "specialist", "admin"))):
    return get_notifications(current_user["id"])


@app.post("/notifications/read")
def mark_read(current_user=Depends(require_roles("employee", "specialist", "admin"))):
    mark_notifications_read(current_user["id"])
    return {"message": "All notifications marked as read."}


# =========================================================
# SPECIALIST KNOWLEDGE BASE CRUD
# =========================================================

@app.get("/specialist/knowledge")
def list_knowledge(current_user=Depends(require_roles("specialist", "admin"))):
    return get_it_knowledge()


@app.post("/specialist/knowledge")
def create_knowledge(req: KnowledgeRequest, current_user=Depends(require_roles("specialist", "admin"))):
    kid = save_it_knowledge(req.category, req.title, req.content, approved_by=current_user["id"])
    return {"message": "IT knowledge article published.", "id": kid}


@app.put("/specialist/knowledge/{knowledge_id}")
def update_knowledge(knowledge_id: int, req: KnowledgeRequest, current_user=Depends(require_roles("specialist", "admin"))):
    success = update_it_knowledge(knowledge_id, req.category, req.title, req.content)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge article not found.")
    return {"message": "Knowledge article updated."}


@app.delete("/specialist/knowledge/{knowledge_id}")
def remove_knowledge(knowledge_id: int, current_user=Depends(require_roles("specialist", "admin"))):
    success = delete_it_knowledge(knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge article not found.")
    return {"message": "Knowledge article deleted."}


# =========================================================
# ADMIN AUDIT & APPROVAL ENDPOINTS
# =========================================================

@app.get("/admin/users")
def list_all_users(current_user=Depends(require_roles("admin"))):
    return get_users()


@app.delete("/admin/users/{user_id}")
def remove_user(user_id: int, current_user=Depends(require_roles("admin"))):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User deleted successfully."}


@app.post("/admin/approve-reply")
def approve_reply(req: ApproveReplyRequest, current_user=Depends(require_roles("admin"))):
    knowledge_id = approve_latest_ticket_reply(req.ticket_id, current_user["id"])
    if not knowledge_id:
        raise HTTPException(status_code=400, detail="No pending reply found for approval.")
    return {
        "message": "Ticket resolution verified and saved to the Enterprise Knowledge Base!",
        "knowledge_id": knowledge_id
    }


@app.get("/admin/stats")
def get_stats(current_user=Depends(require_roles("admin"))):
    tickets = get_tickets()
    users = get_users()
    chats = get_chat_history()
    knowledge = get_it_knowledge()

    total_tickets = len(tickets)
    resolved_tickets = sum(1 for t in tickets if t.get("status") == "resolved")
    open_tickets = sum(1 for t in tickets if t.get("status") == "open")

    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for t in tickets:
        p = t.get("priority", "Medium")
        if p in priority_counts:
            priority_counts[p] += 1

    return {
        "total_tickets": total_tickets,
        "resolved_tickets": resolved_tickets,
        "open_tickets": open_tickets,
        "total_users": len(users),
        "total_chats": len(chats),
        "knowledge_articles": len(knowledge),
        "priority_distribution": priority_counts
    }

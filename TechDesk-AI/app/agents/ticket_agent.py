from app.database.database import save_ticket

# =========================================================
# TICKET GENERATION AGENT
# =========================================================

def create_ticket(
    question: str,
    intent: str = "general",
    department: str = "General IT Helpdesk",
    priority: str = "Medium",
    user_id: int = None
) -> dict:
    ticket_id = save_ticket(
        question=question.strip(),
        intent=intent,
        department=department,
        priority=priority,
        user_id=user_id
    )

    return {
        "ticket_id": ticket_id,
        "question": question.strip(),
        "intent": intent,
        "department": department,
        "priority": priority,
        "status": "open"
    }

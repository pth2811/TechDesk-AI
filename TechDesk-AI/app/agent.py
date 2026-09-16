import re
from app.agents.intent_agent import detect_intent
from app.agents.entity_agent import extract_entities
from app.agents.priority_agent import determine_priority
from app.agents.it_routing_agent import route_to_department
from app.agents.retrieval_agent import retrieve_knowledge
from app.agents.decision_agent import make_decision
from app.agents.ticket_agent import create_ticket


def run_agent(question: str, user_id: int = None) -> dict:
    """
    Main Multi-Agent Workflow for TechDesk AI:
    1. Intent Classification
    2. Entity Extraction
    3. Priority & Urgency Assessment
    4. IT Department Routing
    5. Knowledge Retrieval (DB approved knowledge + RAG)
    6. Resolution Decision & Auto-Ticketing
    """
    q = question.strip()
    if not q:
        return {
            "answer": "Please enter your IT question or issue.",
            "status": "empty",
            "confidence": 0.0,
            "priority": "Low",
            "department": "General IT Helpdesk",
            "ticket_id": None
        }

    # Step 1: Detect Intent
    intent = detect_intent(q)

    # Step 2: Extract Entities
    entities = extract_entities(q)

    # Step 3: Determine Priority
    priority = determine_priority(q, intent)

    # Step 4: Route Department
    department = route_to_department(intent, priority)

    # Problem keywords check (e.g. laptop broken, VPN down, screen shattered)
    problem_words = [
        "broken", "damaged", "error", "failed", "crash", "not working",
        "cannot connect", "can't connect", "won't boot", "won't start",
        "stolen", "lost", "corrupted", "blank", "flickering", "swelling"
    ]
    is_direct_problem = any(w in q.lower() for w in problem_words)

    # Step 5: Knowledge Retrieval
    retrieved = retrieve_knowledge(q)

    # Step 6: Decision
    decision = make_decision(retrieved, is_problem_inquiry=is_direct_problem)

    # If it's a direct hardware or technical problem, or if no knowledge found -> Create Ticket!
    if decision == "ticket" or not retrieved:
        ticket = create_ticket(
            question=q,
            intent=intent,
            department=department,
            priority=priority,
            user_id=user_id
        )
        ticket_id = ticket["ticket_id"]

        if is_direct_problem:
            answer = (
                f"Your issue has been logged as a {priority} Priority ticket ({ticket_id}). "
                f"It has been routed to the {department} team. A specialist will follow up shortly."
            )
        else:
            answer = (
                f"AI could not find a confirmed solution in the knowledge base, so support ticket "
                f"{ticket_id} ({priority} Priority) has been created automatically for {department}."
            )

        return {
            "answer": answer,
            "status": "ticket_created",
            "confidence": 1.0,
            "source": "ticket_system",
            "intent": intent,
            "priority": priority,
            "department": department,
            "entities": entities,
            "ticket_id": ticket_id
        }

    # Answer from knowledge base found
    first_result = retrieved[0]
    answer_text = first_result.get("text", str(first_result))
    score = first_result.get("score", 0.95)

    return {
        "answer": answer_text,
        "status": "answered",
        "confidence": round(float(score), 2),
        "source": first_result.get("source", "it_knowledge_base"),
        "intent": intent,
        "priority": priority,
        "department": department,
        "entities": entities,
        "ticket_id": None
    }

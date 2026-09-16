from app.database.database import get_approved_knowledge_answer
from app.rag import search_knowledge

# =========================================================
# DUAL-LAYER RETRIEVAL AGENT
# =========================================================

def retrieve_knowledge(question: str) -> list:
    """
    1. First search admin-approved IT knowledge base in the database.
    2. If not found, run semantic / keyword search over enterprise RAG documents.
    """
    if not question:
        return []

    # 1. Specialist & Admin Approved Knowledge in DB
    try:
        approved = get_approved_knowledge_answer(question)
        if approved:
            return [{
                "text": approved["answer"],
                "source": "approved_specialist_knowledge",
                "department": approved.get("department", "IT Support"),
                "score": 1.0
            }]
    except Exception as e:
        print(f"Error checking approved knowledge: {e}")

    # 2. Enterprise RAG Knowledge Base
    try:
        rag_results = search_knowledge(question, top_k=2)
        if rag_results:
            return rag_results
    except Exception as e:
        print(f"Error in RAG retrieval: {e}")

    return []

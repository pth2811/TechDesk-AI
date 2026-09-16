# =========================================================
# DECISION AGENT
# =========================================================

def make_decision(results: list, is_problem_inquiry: bool = False) -> str:
    """
    Decides whether the inquiry can be resolved with existing knowledge
    or whether a support ticket must be created.
    """
    if is_problem_inquiry:
        return "ticket"

    if results and len(results) > 0:
        return "answer"

    return "ticket"

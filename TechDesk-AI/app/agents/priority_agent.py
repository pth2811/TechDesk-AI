import re

# =========================================================
# PRIORITY & URGENCY CLASSIFICATION AGENT
# =========================================================

def determine_priority(question: str, intent: str = "general") -> str:
    """
    Evaluates the inquiry text and classifies ticket urgency:
    - Critical: Production outage, security incident, data breach, locked out executive
    - High: Hardware failure, broken laptop, VPN down before deadline, 2FA lost
    - Medium: Software installation, access permission, slow performance
    - Low: General inquiry, guide lookup, how-to question
    """
    q = question.lower().strip()

    critical_keywords = [
        "emergency", "critical", "data breach", "ransomware", "virus", "hacked",
        "system down", "outage", "production down", "leak", "compromised",
        "entire office", "whole team", "server crash", "server down"
    ]
    if any(k in q for k in critical_keywords):
        return "Critical"

    high_keywords = [
        "urgent", "asap", "immediately", "broken", "cracked", "screen broken",
        "battery swelling", "smoke", "spilled", "water damage", "not turning on",
        "won't turn on", "locked out", "lost phone", "lost authenticator",
        "deadline", "cannot work", "can't work", "blocking"
    ]
    if any(k in q for k in high_keywords):
        return "High"

    medium_keywords = [
        "slow", "error", "failing", "failed", "license", "permission", "access",
        "install", "not syncing", "stuck", "bug", "glitch", "issue", "trouble",
        "problem", "cannot connect", "can't connect", "vpn error"
    ]
    if any(k in q for k in medium_keywords) or intent in ["hardware", "software", "network_vpn"]:
        return "Medium"

    return "Low"

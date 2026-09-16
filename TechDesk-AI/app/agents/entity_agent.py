import re

# =========================================================
# IT ENTITY EXTRACTION AGENT
# =========================================================

def extract_entities(question: str) -> dict:
    entities = {}

    # Operating Systems
    os_matches = re.findall(r"\b(macOS|mac|windows\s*1[01]|windows|linux|ubuntu|ios|android)\b", question, re.IGNORECASE)
    if os_matches:
        entities["os"] = list(set([m.lower() for m in os_matches]))

    # Software Applications
    apps = [
        "slack", "zoom", "teams", "docker", "outlook", "excel", "word",
        "globalprotect", "openvpn", "chrome", "vscode", "visual studio",
        "jira", "confluence", "github"
    ]
    found_apps = [app for app in apps if app in question.lower()]
    if found_apps:
        entities["software"] = found_apps

    # Asset Tags (e.g. ASSET-1234, TAG-9988, SN: 12345)
    asset_matches = re.findall(r"\b(?:asset|tag|sn|serial)[:\s-]*([a-zA-Z0-9_-]{4,15})\b", question, re.IGNORECASE)
    if asset_matches:
        entities["asset_tag"] = asset_matches

    # Error Codes (e.g. 0x80070005, Error 403, 502 Bad Gateway)
    error_codes = re.findall(r"\b(?:0x[0-9a-fA-F]+|error\s*\d{3,5}|code\s*\d+)\b", question, re.IGNORECASE)
    if error_codes:
        entities["error_code"] = error_codes

    return entities

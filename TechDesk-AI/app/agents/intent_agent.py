import re

# =========================================================
# IT INTENT RECOGNITION AGENT
# =========================================================

def detect_intent(question: str) -> str:
    q = question.lower().strip()

    # Network & VPN
    network_words = [
        "vpn", "globalprotect", "openvpn", "wifi", "wi-fi", "internet", "network",
        "ethernet", "ip address", "dns", "gateway", "connect to wifi", "bandwidth"
    ]
    if any(w in q for w in network_words):
        return "network_vpn"

    # Hardware & Devices
    hardware_words = [
        "laptop", "screen", "battery", "charger", "keyboard", "mouse", "monitor",
        "docking station", "hardware", "broken screen", "trackpad", "webcam",
        "headset", "audio jack", "power adapter", "loaner laptop"
    ]
    if any(w in q for w in hardware_words):
        return "hardware"

    # Access & Security
    security_words = [
        "password", "mfa", "2fa", "authenticator", "yubikey", "phishing", "suspicious",
        "hack", "locked out", "reset password", "security code", "permission", "access denied"
    ]
    if any(w in q for w in security_words):
        return "access_security"

    # Software & Applications
    software_words = [
        "slack", "teams", "zoom", "docker", "vs code", "visual studio", "office",
        "outlook", "excel", "license", "install software", "syncing", "update software",
        "jetbrains", "github", "jira", "confluence"
    ]
    if any(w in q for w in software_words):
        return "software"

    # General IT / Workplace
    return "general"

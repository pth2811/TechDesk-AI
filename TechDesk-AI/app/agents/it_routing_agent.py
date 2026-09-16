# =========================================================
# IT DEPARTMENT ROUTING AGENT
# =========================================================

def route_to_department(intent: str, priority: str = "Medium") -> str:
    """
    Routes an issue to the corresponding IT operational team based on intent & priority.
    """
    intent = str(intent).lower().strip()

    if priority == "Critical":
        return "SecOps & Emergency IT"

    routing = {
        "network_vpn": "Infrastructure & Network",
        "vpn": "Infrastructure & Network",
        "wifi": "Infrastructure & Network",
        "network": "Infrastructure & Network",

        "hardware": "Workplace Hardware Support",
        "laptop": "Workplace Hardware Support",
        "screen": "Workplace Hardware Support",

        "access_security": "SecOps & Access Control",
        "security": "SecOps & Access Control",
        "password": "SecOps & Access Control",
        "mfa": "SecOps & Access Control",

        "software": "Cloud & Software Licensing",
        "license": "Cloud & Software Licensing",

        "general": "General IT Helpdesk"
    }

    return routing.get(intent, "General IT Helpdesk")

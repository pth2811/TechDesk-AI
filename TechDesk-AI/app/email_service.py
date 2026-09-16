import os
import urllib.request
import json

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip()
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "support@techdesk.local").strip()


def send_email_api(to_email: str, subject: str, html_content: str):
    """Sends email via Brevo REST API if configured, otherwise prints to console."""
    if not to_email:
        return False

    if not BREVO_API_KEY:
        print("==================================================")
        print(f"[EMAIL NOTIFICATION (MOCK)]: To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{html_content}")
        print("==================================================")
        return True

    try:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = {
            "sender": {"name": "TechDesk AI", "email": SENDER_EMAIL},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status in [200, 201]
    except Exception as e:
        print(f"Email delivery error for {to_email}: {e}")
        return False


def send_ticket_created_email(to_email: str, ticket_id: str, question: str, department: str, priority: str = "Medium"):
    subject = f"[TechDesk AI] IT Ticket Created: {ticket_id} ({priority} Priority)"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #2563eb;">TechDesk AI Support Request</h2>
        <p>Hello,</p>
        <p>Your support ticket has been received and routed to the <strong>{department}</strong> team.</p>
        <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 15px 0;">
            <p><strong>Ticket ID:</strong> {ticket_id}</p>
            <p><strong>Priority:</strong> <span style="color: {'#dc2626' if priority in ['High', 'Critical'] else '#2563eb'}; font-weight: bold;">{priority}</span></p>
            <p><strong>Inquiry / Issue:</strong> {question}</p>
            <p><strong>Status:</strong> Open</p>
        </div>
        <p>An IT Specialist will review your request shortly. You can track progress on your Employee Dashboard.</p>
        <p style="color: #64748b; font-size: 12px; margin-top: 25px;">TechDesk AI &bull; Enterprise IT Help Desk &bull; Automated Notification</p>
    </div>
    """
    return send_email_api(to_email, subject, html)


def send_ticket_status_email(to_email: str, ticket_id: str, new_status: str, reply_text: str = ""):
    subject = f"[TechDesk AI] Ticket {ticket_id} Status Updated: {new_status.title()}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #0f766e;">TechDesk AI Ticket Update</h2>
        <p>Hello,</p>
        <p>Your ticket <strong>{ticket_id}</strong> has been marked as <strong>{new_status.upper()}</strong>.</p>
        {f'<div style="background: #f0fdf4; padding: 12px; border-left: 4px solid #16a34a; margin: 15px 0;"><strong>IT Specialist Response:</strong><p>{reply_text}</p></div>' if reply_text else ''}
        <p>Please log in to your dashboard to view the full resolution or provide feedback.</p>
        <p style="color: #64748b; font-size: 12px; margin-top: 25px;">TechDesk AI &bull; Enterprise IT Help Desk</p>
    </div>
    """
    return send_email_api(to_email, subject, html)

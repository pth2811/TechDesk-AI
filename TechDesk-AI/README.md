# TechDesk AI - Enterprise IT Service Desk & Autonomous Multi-Agent Support Portal

A modern, cloud-ready enterprise IT helpdesk system powered by **FastAPI**, **SQLite/PostgreSQL**, **RAG (Retrieval-Augmented Generation)**, and an **Autonomous Multi-Agent Workflow**.

---

## Key Differentiations from Original Campus Help Desk

| Dimension | Original Project (`AI-Help-Desk`) | Differentiated Project (`TechDesk-AI`) |
| :--- | :--- | :--- |
| **Domain** | College Campus Support (Silver Oak University) | **Enterprise IT & Workplace Operations** |
| **User Roles** | Student, Faculty, Admin | **Employee, IT Specialist, System Administrator** |
| **Ticket Priority** | None / Fixed | **Dynamic Priority Agent (Critical, High, Medium, Low)** |
| **Multi-Agent Pipeline** | Intent, Entity, Retrieval, Decision, Faculty, Ticket | **Intent, Entity, Priority, IT Routing, Retrieval, Decision, Ticket** |
| **Knowledge Base** | Exam timetable, college fees, campus hostel | **Corporate VPN, 802.1X Wi-Fi, 2FA/MFA, Laptop swaps, Software licenses** |
| **User Interface** | Monolithic 4000+ line HTML files | **Modular CSS/JS architecture, dark cyber glassmorphism design** |
| **Feedback System** | None | **Interactive 1–5 Star Resolution Rating System** |
| **Database** | `ai_help_desk.db` | `techdesk.db` (clean schema with priority & rating metrics) |

---

## Multi-Agent System Architecture

When an employee asks an IT question or reports an issue:
1. **Intent Agent** (`app/agents/intent_agent.py`): Categorizes the inquiry into *Hardware*, *Software*, *Network/VPN*, *Access & Security*, or *General IT*.
2. **Entity Agent** (`app/agents/entity_agent.py`): Extracts operating systems, applications, asset tags, and error codes.
3. **Priority Agent** (`app/agents/priority_agent.py`): Assesses severity and urgency (*Critical*, *High*, *Medium*, *Low*).
4. **IT Routing Agent** (`app/agents/it_routing_agent.py`): Automatically assigns the ticket to *Infrastructure & Network*, *Workplace Hardware*, *SecOps*, *Cloud & Software*, or *General IT*.
5. **Retrieval Agent** (`app/agents/retrieval_agent.py`): Searches both verified specialist knowledge in the database and enterprise RAG documents.
6. **Decision Agent** (`app/agents/decision_agent.py`): Determines whether the question can be immediately answered or requires a support ticket.
7. **Ticket Agent** (`app/agents/ticket_agent.py`): Automatically generates a uniquely numbered ticket (e.g. `TECH-YYYYMMDD-XXXX`) and dispatches notifications.

---

## Quick Start & Setup (Windows)

### 1. Open Terminal in the `TechDesk-AI` folder
```powershell
cd c:\Users\Parth\Desktop\TechDesk-AI
```

### 2. Set Up Python Virtual Environment
You can create a local environment:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
*(Or use the existing virtual environment from `..\AI-Help-Desk\.venv\Scripts\activate`)*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the Application
You can run the server directly using Uvicorn:
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
*Or simply double-click **`run.bat`** on Windows!*

### 5. Access the Web Portals
Open your browser and navigate to:
- **Login / Landing Page**: [http://127.0.0.1:8001](http://127.0.0.1:8001)
- **Registration**: [http://127.0.0.1:8001/register](http://127.0.0.1:8001/register)
- **API Swagger Documentation**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

---

## Role Access Codes & Default Credentials

During registration:
- **Employee**: No access code required. Open to all company staff.
- **IT Specialist**: Access code is **`TECH2026`**
- **System Administrator**: Access code is **`ADMIN2026`**

*(These access codes can be customized anytime in the `.env` file).*

---

## Port Configuration
`TechDesk-AI` defaults to port **`8001`** so that it can run side-by-side with your original project (`8000`) without any port conflicts.

---

## Project Structure

```
TechDesk-AI/
├── .env.example                # Environment template
├── .env                        # Local active configuration
├── .gitignore                  # Git exclusions
├── requirements.txt            # Python dependencies
├── run.bat                     # 1-click Windows runner
├── README.md                   # Full documentation
├── knowledge_base/
│   └── it_knowledge.txt        # Enterprise IT policies and guides
└── app/
    ├── __init__.py
    ├── main.py                 # FastAPI endpoints & application router
    ├── auth.py                 # Authentication, hashing & session security
    ├── agent.py                # Multi-agent coordinator
    ├── rag.py                  # RAG engine (embeddings + fallback)
    ├── email_service.py        # Email alerts & mock console logger
    ├── password_reset.py       # Password recovery workflow
    ├── agents/
    │   ├── intent_agent.py     # IT intent recognition
    │   ├── entity_agent.py     # Entity extractor
    │   ├── priority_agent.py   # Severity & urgency classification
    │   ├── it_routing_agent.py # Team routing
    │   ├── retrieval_agent.py  # Dual-layer search
    │   ├── decision_agent.py   # AI decision maker
    │   └── ticket_agent.py     # Ticket generator
    ├── database/
    │   └── database.py         # SQLite/PostgreSQL schema & CRUD
    └── frontend/
        ├── index.html          # Login portal
        ├── register.html       # Multi-role registration
        ├── employee.html       # Employee AI assistant & ticket status
        ├── specialist.html     # IT Specialist bay & knowledge publisher
        ├── admin.html          # Admin oversight & resolution approval
        ├── password-reset.html # Password reset form
        ├── css/
        │   ├── theme.css       # Design tokens & priority badges
        │   └── dashboard.css   # Dashboard layout & chat bubble styles
        └── js/
            ├── auth.js         # Session verification
            ├── employee.js     # Chat and ticket logic
            ├── specialist.js   # Specialist response & KB publishing
            └── admin.js        # Audit and approval logic
```

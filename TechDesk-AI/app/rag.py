import os
import re
from pathlib import Path

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
TEXT_FILE = KNOWLEDGE_DIR / "it_knowledge.txt"

# Read Knowledge Files
text_parts = []
if TEXT_FILE.exists():
    try:
        text_parts.append(TEXT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading IT knowledge file: {e}")

# Read any PDF in knowledge_base directory
for pdf_file in KNOWLEDGE_DIR.glob("*.pdf"):
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_file))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    except Exception as e:
        print(f"Error reading PDF {pdf_file.name}: {e}")

raw_text = "\n".join(text_parts)
cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

print("====================================")
print("TECHDESK AI - RAG SYSTEM INITIALIZED")
print("Knowledge text loaded:", TEXT_FILE.exists())
print("====================================")

# =========================================================
# EXACT FAST-PATH IT ANSWERS
# =========================================================

EXACT_ANSWERS = {
    "vpn": (
        "To connect to the corporate VPN, launch GlobalProtect, enter the portal address "
        "'vpn.techdesk.internal', log in with your SSO credentials, and approve the 2FA push on your phone. "
        "The shield icon turns solid blue upon successful connection."
    ),
    "wifi": (
        "To connect to office Wi-Fi, select 'TechDesk-Secure', enter your corporate email and domain password, "
        "and accept the security certificate. Visitors can connect to 'TechDesk-Guest' for temporary 8-hour access."
    ),
    "password": (
        "To reset your corporate password, visit the self-service portal at https://id.techdesk.internal/reset. "
        "Passwords must be at least 14 characters long and include uppercase, numbers, and symbols."
    ),
    "mfa": (
        "To configure or transfer 2FA, log in to https://myaccount.techdesk.internal/security, select "
        "'Security Info', and scan the QR code with your Microsoft or Google Authenticator app."
    ),
    "hardware": (
        "For laptop hardware failures, battery swelling, or screen damage, submit an IT Hardware ticket "
        "with your device Serial Number. Loaner laptops and swaps are handled at IT Bay Room B-204."
    ),
    "software": (
        "Standard tools (Slack, Teams, VS Code, Chrome) can be installed from the Company Portal without admin rights. "
        "Paid licenses (Docker Desktop, JetBrains, Adobe) require departmental budget approval."
    ),
    "phishing": (
        "To report a suspicious or phishing email, click the 'Report Phishing' button in the Outlook toolbar. "
        "Do not click links or download attachments. SecOps will inspect the headers immediately."
    )
}

# =========================================================
# EMBEDDINGS & FAISS (WITH GRACEFUL FALLBACK)
# =========================================================

chunks = []
if cleaned_text:
    words = cleaned_text.split()
    chunk_size = 140
    for i in range(0, len(words), chunk_size):
        c = " ".join(words[i:i + chunk_size]).strip()
        if len(c) > 30:
            chunks.append(c)

model = None
index = None

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    if chunks:
        embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        print(f"FAISS index built with {len(chunks)} chunks.")
except Exception as exc:
    print(f"Embedding model/FAISS note (using smart keyword RAG fallback): {exc}")


def keyword_search(question: str, top_k: int = 2) -> list:
    """Smart fallback keyword-overlap search when FAISS is unavailable."""
    if not question or not chunks:
        return []

    q_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", question.lower()))
    scored = []
    for chunk in chunks:
        c_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", chunk.lower()))
        common = q_words & c_words
        if common:
            scored.append({"text": chunk, "score": len(common) / max(len(q_words), 1)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def semantic_search(question: str, top_k: int = 2) -> list:
    if not question:
        return []

    if model is not None and index is not None and chunks:
        try:
            q_emb = model.encode([question], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
            scores, indices = index.search(q_emb, top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0:
                    results.append({"text": chunks[idx], "score": float(score)})
            return results
        except Exception as e:
            print(f"Semantic search error: {e}")

    return keyword_search(question, top_k)


def search_knowledge(question: str, top_k: int = 2) -> list:
    q = question.lower().strip()
    if not q:
        return []

    # 1. Check Exact Curated Answers
    if "vpn" in q or "globalprotect" in q:
        return [{"text": EXACT_ANSWERS["vpn"], "score": 1.0, "source": "exact_match"}]
    if "wifi" in q or "wi-fi" in q or "network connection" in q:
        return [{"text": EXACT_ANSWERS["wifi"], "score": 1.0, "source": "exact_match"}]
    if "reset password" in q or "forgot password" in q or "change password" in q:
        return [{"text": EXACT_ANSWERS["password"], "score": 1.0, "source": "exact_match"}]
    if "mfa" in q or "2fa" in q or "authenticator" in q:
        return [{"text": EXACT_ANSWERS["mfa"], "score": 1.0, "source": "exact_match"}]
    if "phishing" in q or "suspicious email" in q or "scam" in q:
        return [{"text": EXACT_ANSWERS["phishing"], "score": 1.0, "source": "exact_match"}]
    if "license" in q or "docker" in q or "software request" in q:
        return [{"text": EXACT_ANSWERS["software"], "score": 1.0, "source": "exact_match"}]

    # 2. Semantic / Chunk Search
    results = semantic_search(question, top_k=top_k)
    return results

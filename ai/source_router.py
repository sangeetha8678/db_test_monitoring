"""
AI Source Router Module.
Classifies user questions into information sources:
- TELEMETRY (Database / MCP tools)
- RAG (Local technical manuals / documentation)
- WEB (External Internet search)
- GENERAL (Qwen3 general knowledge)
- HYBRID (Multi-source evidence fusion)

The router MUST NOT answer the question itself; its only job is deciding which information source(s) to route to.
"""

import json
import re
from ai.ollama_client import call_ollama

VALID_ROUTES = ["TELEMETRY", "RAG", "WEB", "GENERAL", "HYBRID"]

def classify_information_source(question):
    """
    Classifies question into TELEMETRY, RAG, WEB, GENERAL, or HYBRID.
    Returns dict with route, confidence, reason, and sources list.
    """
    q_clean = question.strip()
    q_lower = q_clean.lower()

    # 1. Try Qwen3 8B Ollama Source Router
    system_prompt = """
    You are an AI Source Router for a Power Telemetry & Analytics Platform.
    Classify the user question into one of these sources:
    - TELEMETRY: Questions about database values, measured energy, power, voltage, current, device telemetry, timestamps, or device comparisons.
    - RAG: Questions about local documentation, user manuals, alarm codes (e.g. Alarm 23), maintenance procedures, or operating guidelines.
    - WEB: Questions asking for external news, latest smart meter developments, current IEEE/IEC standards, or software versions.
    - GENERAL: Questions asking for general physics or electrical definitions (e.g. "What is voltage?", "What is active power?").
    - HYBRID: Questions combining database values with manual/industry guidance (e.g. "Device 1 PF is 0.72, is that low according to our manual?").

    Return strictly a JSON object:
    {
        "route": "<TELEMETRY|RAG|WEB|GENERAL|HYBRID>",
        "confidence": 0.95,
        "reason": "<explanation>",
        "sources": ["TELEMETRY", "RAG", "WEB"]
    }
    DO NOT answer the question itself.
    """

    llm_resp = call_ollama(q_clean, system_prompt=system_prompt, format_json=True, temperature=0.0)
    if llm_resp:
        try:
            parsed = json.loads(llm_resp)
            if parsed.get("route") in VALID_ROUTES:
                if "sources" not in parsed:
                    parsed["sources"] = [parsed["route"]]
                return parsed
        except Exception:
            pass

    # 2. Rule-Based Fallback Source Classifier
    is_telemetry = any(k in q_lower for k in [
        "device", "kwh", "active power", "reactive power", "apparent power", "voltage",
        "current", "frequency", "power factor", "yesterday", "last 6", "last 24", "peak",
        "consumed", "telemetry", "table", "data", "whuch device", "which device"
    ])
    
    is_rag = any(k in q_lower for k in [
        "manual", "doc", "documentation", "alarm", "alarm code", "code 23", "maintenance",
        "procedure", "guidance", "specification", "limit", "operating range"
    ])

    is_web = any(k in q_lower for k in [
        "latest", "web", "internet", "news", "recent development", "standard", "ieee", "iec", "version"
    ])

    if is_telemetry and (is_rag or is_web):
        sources = ["TELEMETRY"]
        if is_rag: sources.append("RAG")
        if is_web: sources.append("WEB")
        return {
            "route": "HYBRID",
            "confidence": 0.92,
            "reason": "Question combines measured telemetry data with manual or external guidance.",
            "sources": sources
        }
    elif is_telemetry:
        return {
            "route": "TELEMETRY",
            "confidence": 0.98,
            "reason": "Question asks for telemetry values from database.",
            "sources": ["TELEMETRY"]
        }
    elif is_rag:
        return {
            "route": "RAG",
            "confidence": 0.95,
            "reason": "Question asks about local documentation, manuals, or alarm procedures.",
            "sources": ["RAG"]
        }
    elif is_web:
        return {
            "route": "WEB",
            "confidence": 0.95,
            "reason": "Question asks for external web/industry information.",
            "sources": ["WEB"]
        }
    else:
        return {
            "route": "GENERAL",
            "confidence": 0.90,
            "reason": "Question asks for general explanation or definition.",
            "sources": ["GENERAL"]
        }

"""
Qwen3 8B Structured Intent & Tool Router Module.
Parses natural language queries into structured JSON intent schemas.
Uses Ollama Qwen3 8B structured JSON mode with low temperature (0.0).
Includes semantic fallback parsing tolerant of user typos.
"""

import json
import re
from ai.ollama_client import call_ollama

VALID_INTENTS = [
    "energy_consumption", "power_analysis", "voltage_analysis", "current_analysis",
    "frequency_analysis", "power_factor_analysis", "device_summary", "list_devices",
    "compare_devices", "compare_periods", "anomaly_analysis", "phase_imbalance",
    "trend_analysis", "correlation_analysis", "device_health", "forecast_power",
    "forecast_energy", "explain_anomaly", "database_summary", "conversation", "unknown"
]

def route_user_intent(question, session_state=None):
    """
    Parses question into structured intent schema using Qwen3 8B LLM.
    """
    q_clean = question.strip()
    q_lower = q_clean.lower()

    # 1. Try Qwen3 8B Ollama Structured Output
    system_prompt = """
    You are Qwen3 8B Structured Intent Router for Telemetry Analytics.
    Analyze the user question and return strictly a JSON object with this schema:
    {
        "intent": "<intent_name>",
        "metric": "<active_power|reactivepower|apparentpower|importenergykwh|voltageab|currentavg|powerfactor|frequency|null>",
        "aggregation": "<average|max|min|count|null>",
        "device_id": "<device_number_string_or_null>",
        "duration_hours": <number_or_null>,
        "comparison_device": "<device_number_string_or_null>",
        "forecast_horizon": <number_or_null>,
        "needs_clarification": false,
        "clarification_question": null
    }

    Supported intents: energy_consumption, power_analysis, voltage_analysis, current_analysis, frequency_analysis, power_factor_analysis, device_summary, list_devices, compare_devices, compare_periods, anomaly_analysis, phase_imbalance, trend_analysis, correlation_analysis, device_health, forecast_power, forecast_energy, explain_anomaly, database_summary, conversation, unknown.
    """

    llm_resp = call_ollama(q_clean, system_prompt=system_prompt, format_json=True, temperature=0.0)
    if llm_resp:
        try:
            parsed = json.loads(llm_resp)
            if parsed.get("intent") in VALID_INTENTS:
                return parsed
        except Exception:
            pass

    # 2. Semantic NLP Fallback Router (Typo-Tolerant)
    device_m = re.search(r"device\s*([0-9]+)", q_lower)
    device_id = device_m.group(1) if device_m else None

    hours = None
    if "6 hrs" in q_lower or "6 hours" in q_lower: hours = 6.0
    elif "24 hrs" in q_lower or "24 hours" in q_lower or "today" in q_lower: hours = 24.0
    elif "48 hrs" in q_lower or "yesterday" in q_lower: hours = 48.0

    # Device Identity Inquiry Check ("whuch device", "which device", "what device")
    if any(phrase in q_lower for phrase in ["which device", "whuch device", "wich device", "what device", "device id"]):
        return {
            "intent": "device_summary",
            "metric": None,
            "aggregation": None,
            "device_id": session_state.state.get("last_device") if session_state else "1",
            "duration_hours": hours,
            "is_identity_query": True
        }

    # Intent matching
    if any(k in q_lower for k in ["list device", "devices", "show devices"]):
        intent = "list_devices"
    elif any(k in q_lower for k in ["health", "status", "condition"]):
        intent = "device_health"
    elif any(k in q_lower for k in ["anomal", "outlier", "abnormal", "spike"]):
        intent = "anomaly_analysis"
    elif any(k in q_lower for k in ["forecast", "predict", "future"]):
        intent = "forecast_power"
    elif any(k in q_lower for k in ["compare", "versus", "vs"]):
        intent = "compare_devices"
    elif any(k in q_lower for k in ["imbalance", "unbalance", "phase"]):
        intent = "phase_imbalance"
    elif any(k in q_lower for k in ["trend", "direction", "slope"]):
        intent = "trend_analysis"
    elif any(k in q_lower for k in ["correlat", "relationship"]):
        intent = "correlation_analysis"
    elif any(k in q_lower for k in ["energy", "kwh", "consumed", "engery"]):
        intent = "energy_consumption"
    elif any(k in q_lower for k in ["power", "kw", "load", "powr"]):
        intent = "power_analysis"
    elif any(k in q_lower for k in ["voltage", "volts", "volt"]):
        intent = "voltage_analysis"
    elif any(k in q_lower for k in ["current", "amps", "amp"]):
        intent = "current_analysis"
    elif any(k in q_lower for k in ["hi", "hello", "hey"]):
        intent = "conversation"
    else:
        intent = "power_analysis" if device_id else "database_summary"

    return {
        "intent": intent,
        "metric": "active_power",
        "aggregation": "average",
        "device_id": device_id,
        "duration_hours": hours,
        "comparison_device": "2" if intent == "compare_devices" else None,
        "forecast_horizon": 6 if intent == "forecast_power" else None,
        "needs_clarification": False,
        "clarification_question": None
    }

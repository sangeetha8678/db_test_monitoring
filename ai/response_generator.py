"""
Qwen3 Multi-Source Evidence Response Generator Module.
Generates evidence-based, natural language explanations grounded in Telemetry, RAG, Web Search, and General Knowledge.
Does NOT recalculate telemetry numbers.
"""

from ai.ollama_client import call_ollama

def generate_evidence_based_explanation(question, route_info=None, telemetry_result=None, rag_result=None, web_result=None, session_state=None):
    """
    Produces concise, evidence-grounded explanation based on the active routing sources.
    """
    route = route_info.get("route", "TELEMETRY") if route_info else "TELEMETRY"

    # Direct Identity Follow-Up Check
    if telemetry_result and (telemetry_result.get("is_identity_query") or "calculated for Device" in str(telemetry_result.get("answer", ""))):
        dev_id = session_state.state.get("last_device", "1") if session_state else "1"
        return f"That result was calculated for **Device {dev_id}**."

    evidence_parts = []

    # 1. Telemetry Evidence
    if telemetry_result and telemetry_result.get("success"):
        ans = telemetry_result.get("answer", "")
        if ans:
            evidence_parts.append(f"[Telemetry Database Evidence]\n{ans}")

    # 2. RAG Knowledge Base Evidence
    if rag_result and rag_result.get("success") and rag_result.get("context_text"):
        evidence_parts.append(f"[Local Manual / Documentation Evidence]\n{rag_result['context_text']}")

    # 3. Web Search Evidence
    if web_result and web_result.get("success"):
        src = web_result.get("source", "Web Search")
        sum_txt = web_result.get("summary", "")
        evidence_parts.append(f"[{src}]\n{sum_txt}")

    # If pure TELEMETRY route and we have direct answer, return it cleanly
    if route == "TELEMETRY" and telemetry_result and telemetry_result.get("answer"):
        return telemetry_result["answer"]

    # If pure RAG route and no LLM available, return direct excerpt
    if route == "RAG" and rag_result and rag_result.get("context_text"):
        excerpts = rag_result.get("excerpts", [])
        if excerpts:
            return f"According to **{excerpts[0]['source']}**:\n\n{excerpts[0]['text']}"

    # If pure WEB route
    if route == "WEB" and web_result and web_result.get("summary"):
        return f"**{web_result.get('source', 'Web Search')}**:\n\n{web_result['summary']}"

    # Multi-source evidence fusion via Qwen3 8B
    system_prompt = """
    You are an intelligent AI Telemetry & Analytics Assistant (powered by Qwen3 8B, MCP, and RAG).
    Answer the user question clearly and concisely based strictly on the provided evidence sources.
    Do NOT recalculate telemetry numbers or invent facts not present in the evidence.
    """

    combined_evidence = "\n\n".join(evidence_parts) if evidence_parts else "No specific database or documentation evidence retrieved."
    prompt = f"User Question: {question}\n\nRetrieved Evidence:\n{combined_evidence}"

    llm_resp = call_ollama(prompt, system_prompt=system_prompt, temperature=0.0)
    if llm_resp and len(llm_resp.strip()) > 10:
        return llm_resp.strip()

    # Fallback to evidence text
    if evidence_parts:
        return "\n\n".join(evidence_parts)

    return "Analyzed your inquiry. Please specify if you would like telemetry data, manual documentation, or web research."

"""
Ollama Local LLM Client Module.
Communicates with Qwen3 8B at http://localhost:11434/api/generate.
"""

import json
import urllib.request
from config import OLLAMA_URL, QWEN_MODEL, LLM_TEMPERATURE

def call_ollama(prompt, system_prompt=None, format_json=False, temperature=LLM_TEMPERATURE):
    """
    Sends a request to local Ollama Qwen3 8B. Returns raw response text or None if unreachable.
    """
    url = f"{OLLAMA_URL}/api/generate"
    full_prompt = f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
    
    payload_dict = {
        "model": QWEN_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    if format_json:
        payload_dict["format"] = "json"

    try:
        data = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json.get("response", "").strip()
    except Exception:
        return None

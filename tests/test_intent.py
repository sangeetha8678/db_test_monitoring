"""
Intent Routing Test Suite.
Verifies structured intent routing across standard, typo, and follow-up questions.
"""

from ai.intent_router import route_user_intent
from ai.conversation_state import ConversationSessionState

def test_intent_routing():
    print("🧪 Running Intent Routing Tests...")
    
    # 1. Standard Query
    res1 = route_user_intent("Average active power for Device 1 last 6 hours")
    assert res1["intent"] == "power_analysis", f"Expected power_analysis, got {res1['intent']}"
    assert res1["device_id"] == "1", f"Expected device_id 1, got {res1['device_id']}"
    print("  ✓ Standard Query Test Passed")

    # 2. Typo Query
    res2 = route_user_intent("engery consumed for device 2")
    assert res2["intent"] == "energy_consumption", f"Expected energy_consumption, got {res2['intent']}"
    print("  ✓ Typo Query Test Passed")

    # 3. Device Identity Follow-up Query
    state = ConversationSessionState()
    state.update({"device_id": "1", "metric": "active_power"})
    res3 = route_user_intent("for whuch device", session_state=state)
    assert res3["intent"] == "device_summary", f"Expected device_summary, got {res3['intent']}"
    print("  ✓ Device Identity Follow-up Test Passed")

    print("✅ All Intent Routing Tests Passed Successfully!")

if __name__ == "__main__":
    test_intent_routing()

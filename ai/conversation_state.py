"""
Structured Conversation Memory & Session State Module.
Maintains structured server-side state (last_device, last_metric, last_aggregation, last_duration_hours, last_intent)
to resolve context and follow-up queries across chat turns.
"""

class ConversationSessionState:
    def __init__(self):
        self.state = {
            "last_device": "1",
            "last_metric": "active_power",
            "last_aggregation": "average",
            "last_duration_hours": None,
            "last_intent": "power_analysis",
            "last_result_type": "power_metrics",
            "last_answer": ""
        }

    def update(self, intent_data, answer=""):
        if intent_data.get("device_id"):
            self.state["last_device"] = str(intent_data["device_id"])
        if intent_data.get("metric"):
            self.state["last_metric"] = str(intent_data["metric"])
        if intent_data.get("aggregation"):
            self.state["last_aggregation"] = str(intent_data["aggregation"])
        if intent_data.get("duration_hours") is not None:
            self.state["last_duration_hours"] = intent_data["duration_hours"]
        if intent_data.get("intent"):
            self.state["last_intent"] = str(intent_data["intent"])
        if answer:
            self.state["last_answer"] = answer

    def resolve_followup(self, intent_data):
        """
        Inherits previous session state parameters if missing from current intent.
        """
        resolved = dict(intent_data)
        if not resolved.get("device_id") and self.state.get("last_device"):
            resolved["device_id"] = self.state["last_device"]
        if not resolved.get("metric") and self.state.get("last_metric"):
            resolved["metric"] = self.state["last_metric"]
        if not resolved.get("aggregation") and self.state.get("last_aggregation"):
            resolved["aggregation"] = self.state["last_aggregation"]
        if resolved.get("duration_hours") is None and self.state.get("last_duration_hours") is not None:
            resolved["duration_hours"] = self.state["last_duration_hours"]
        return resolved

    def to_json(self):
        return dict(self.state)

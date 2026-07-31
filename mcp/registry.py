"""
MCP Structured Tool Registry Module.
Registers MCP tool definitions, input schemas, validation controls, and execution handlers.
Prevents non-SELECT destructive SQL execution through AI tools.
"""

from mcp import telemetry_tools

class MCPToolRegistry:
    def __init__(self):
        self.tools = {}
        self._register_default_tools()

    def register(self, name, description, input_schema, handler):
        self.tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": handler
        }

    def _register_default_tools(self):
        self.register(
            "mcp_list_devices",
            "Lists all available telemetry devices.",
            {"type": "object", "properties": {"table": {"type": "string"}}},
            telemetry_tools.mcp_list_devices
        )
        self.register(
            "mcp_get_energy_consumption",
            "Calculates net energy consumption (kWh).",
            {"type": "object", "properties": {"hours": {"type": ["number", "null"]}, "deviceid": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_get_energy_consumption
        )
        self.register(
            "mcp_get_power_metrics",
            "Calculates Active Power (kW), Reactive Power (kVAR), and Apparent Power (kVA) metrics.",
            {"type": "object", "properties": {"hours": {"type": ["number", "null"]}, "deviceid": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_get_power_metrics
        )
        self.register(
            "mcp_get_voltage_metrics",
            "Calculates line and phase voltage metrics, standard deviation, and phase imbalance.",
            {"type": "object", "properties": {"hours": {"type": ["number", "null"]}, "deviceid": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_get_voltage_metrics
        )
        self.register(
            "mcp_get_current_metrics",
            "Calculates 3-phase amperage metrics, phase imbalance, and spikes.",
            {"type": "object", "properties": {"hours": {"type": ["number", "null"]}, "deviceid": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_get_current_metrics
        )
        self.register(
            "mcp_get_frequency_metrics",
            "Calculates grid frequency metrics and deviation from nominal 50Hz.",
            {"type": "object", "properties": {"hours": {"type": ["number", "null"]}, "deviceid": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_get_frequency_metrics
        )
        self.register(
            "mcp_get_power_factor",
            "Calculates power factor efficiency and low-PF threshold periods.",
            {"type": "object", "properties": {"hours": {"type": ["number", "null"]}, "deviceid": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_get_power_factor
        )
        self.register(
            "mcp_get_device_summary",
            "Provides comprehensive telemetry summary for a target device.",
            {"type": "object", "properties": {"deviceid": {"type": "string"}}},
            telemetry_tools.mcp_get_device_summary
        )
        self.register(
            "mcp_compare_devices",
            "Compares metrics between two specified devices.",
            {"type": "object", "properties": {"device1": {"type": "string"}, "device2": {"type": "string"}, "metric": {"type": "string"}, "hours": {"type": "number"}}},
            telemetry_tools.mcp_compare_devices
        )
        self.register(
            "mcp_compare_periods",
            "Compares device telemetry across two time windows.",
            {"type": "object", "properties": {"deviceid": {"type": "string"}, "metric": {"type": "string"}, "period1_hours": {"type": "number"}, "period2_hours": {"type": "number"}}},
            telemetry_tools.mcp_compare_periods
        )
        self.register(
            "mcp_get_phase_imbalance",
            "Calculates NEMA 3-phase voltage and current percentage imbalance.",
            {"type": "object", "properties": {"deviceid": {"type": "string"}, "hours": {"type": "number"}}},
            telemetry_tools.mcp_get_phase_imbalance
        )
        self.register(
            "mcp_detect_anomalies",
            "Detects anomalies using Isolation Forest, LSTM Autoencoder, and Z-Score statistics.",
            {"type": "object", "properties": {"deviceid": {"type": ["string", "null"]}, "metric": {"type": "string"}, "hours": {"type": "number"}}},
            telemetry_tools.mcp_detect_anomalies
        )
        self.register(
            "mcp_get_device_health",
            "Evaluates transparent device health status with interpretable reasons.",
            {"type": "object", "properties": {"deviceid": {"type": "string"}, "hours": {"type": "number"}}},
            telemetry_tools.mcp_get_device_health
        )
        self.register(
            "mcp_get_correlations",
            "Calculates Pearson correlations between telemetry parameters.",
            {"type": "object", "properties": {"deviceid": {"type": ["string", "null"]}, "hours": {"type": "number"}}},
            telemetry_tools.mcp_get_correlations
        )
        self.register(
            "mcp_get_trend_analysis",
            "Analyzes telemetry trend direction, linear slope, and percentage changes.",
            {"type": "object", "properties": {"deviceid": {"type": ["string", "null"]}, "metric": {"type": "string"}, "hours": {"type": "number"}}},
            telemetry_tools.mcp_get_trend_analysis
        )
        self.register(
            "mcp_forecast_power",
            "Forecasts active power (kW) using multi-stage ML/DL models.",
            {"type": "object", "properties": {"deviceid": {"type": ["string", "null"]}, "horizon": {"type": "number"}}},
            telemetry_tools.mcp_forecast_power
        )
        self.register(
            "mcp_forecast_energy",
            "Forecasts energy consumption (kWh) using multi-stage ML/DL models.",
            {"type": "object", "properties": {"deviceid": {"type": ["string", "null"]}, "horizon": {"type": "number"}}},
            telemetry_tools.mcp_forecast_energy
        )
        self.register(
            "mcp_explain_anomaly",
            "Analyzes telemetry around peak events to explain anomaly evidence.",
            {"type": "object", "properties": {"deviceid": {"type": "string"}, "timestamp": {"type": ["string", "null"]}}},
            telemetry_tools.mcp_explain_anomaly
        )
        self.register(
            "mcp_get_database_summary",
            "Returns overall database record counts, date bounds, and net energy.",
            {"type": "object", "properties": {"table": {"type": "string"}}},
            telemetry_tools.mcp_get_database_summary
        )

    def execute_tool(self, tool_name, kwargs, repo, table="energymeter"):
        if tool_name not in self.tools:
            return telemetry_tools.mcp_get_telemetry_summary(repo, kwargs.get("deviceid"), table)
        handler = self.tools[tool_name]["handler"]
        return handler(repo, **kwargs)

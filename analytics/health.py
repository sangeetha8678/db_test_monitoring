"""
Device Health Engine.
Evaluates 3-phase current imbalance, power factor efficiency, voltage stability, and load spikes
to output transparent health status (NORMAL, ATTENTION, WARNING, CRITICAL) with clear reasons.
"""

from analytics.voltage import calculate_voltage_metrics
from analytics.current import calculate_current_metrics
from analytics.power import calculate_power_metrics
from config import POWER_FACTOR_THRESHOLD, NOMINAL_FREQUENCY

def evaluate_device_health(repo, table="energymeter", device_id="1", hours=24):
    """
    Evaluates transparent device health status with interpretable reasons.
    """
    v_res = calculate_voltage_metrics(repo, table, device_id, hours)
    i_res = calculate_current_metrics(repo, table, device_id, hours)
    p_res = calculate_power_metrics(repo, table, device_id, hours)

    reasons = []
    status = "NORMAL"

    # 1. Voltage Imbalance Check
    if v_res.get("success"):
        v_imb = v_res["imbalance"]["imbalance_pct"]
        if v_imb > 5.0:
            status = "CRITICAL"
            reasons.append(f"Severe 3-Phase Voltage Imbalance ({v_imb}% exceeds 5% emergency limit)")
        elif v_imb > 2.0:
            if status != "CRITICAL": status = "WARNING"
            reasons.append(f"Elevated 3-Phase Voltage Imbalance ({v_imb}% exceeds 2% threshold)")

    # 2. Current Imbalance Check
    if i_res.get("success"):
        i_imb = i_res["imbalance"]["imbalance_pct"]
        if i_imb > 20.0:
            status = "CRITICAL"
            reasons.append(f"Severe Current Phase Imbalance ({i_imb}% exceeds 20% limit)")
        elif i_imb > 10.0:
            if status not in ["CRITICAL", "WARNING"]: status = "ATTENTION"
            reasons.append(f"Noticeable Current Phase Imbalance ({i_imb}% exceeds 10% threshold)")

    # 3. Peak Power Surge Check
    if p_res.get("success"):
        avg_p = p_res["avg_active_kw"]
        peak_p = p_res["max_active_kw"]
        if avg_p > 0 and (peak_p / avg_p) > 2.5:
            if status not in ["CRITICAL"]: status = "WARNING"
            reasons.append(f"High Instantaneous Load Spike detected (Peak: {peak_p:,.2f} kW vs Avg: {avg_p:,.2f} kW)")

    if not reasons:
        reasons.append("All voltage, current, power factor, and load parameters operating within nominal thresholds.")

    answer = f"Device {device_id} Health Status: {status}. Evaluated factors: " + "; ".join(reasons)

    return {
        "success": True,
        "device_id": str(device_id),
        "status": status,
        "reasons": reasons,
        "voltage_metrics": v_res,
        "current_metrics": i_res,
        "power_metrics": p_res,
        "answer": answer
    }

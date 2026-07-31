"""
Phase Imbalance Analytics Module.
Calculates NEMA-compliant percentage imbalance for 3-phase voltage and current telemetry.
"""

from config import VOLTAGE_IMBALANCE_THRESHOLD, CURRENT_IMBALANCE_THRESHOLD

def calculate_nema_imbalance(v1, v2, v3):
    """
    Calculates NEMA percentage imbalance:
    Imbalance (%) = (Max deviation from average / Average) * 100
    """
    vals = [v for v in [v1, v2, v3] if v is not None]
    if not vals or len(vals) < 3:
        return {"imbalance_pct": 0.0, "avg": 0.0, "max_dev": 0.0, "affected_phase": None}
    
    avg_val = sum(vals) / float(len(vals))
    if avg_val == 0:
        return {"imbalance_pct": 0.0, "avg": 0.0, "max_dev": 0.0, "affected_phase": None}

    deviations = [abs(val - avg_val) for val in vals]
    max_dev = max(deviations)
    max_idx = deviations.index(max_dev)
    phase_names = ["Phase A / AB", "Phase B / BC", "Phase C / CA"]
    
    imbalance_pct = (max_dev / avg_val) * 100.0
    return {
        "imbalance_pct": round(imbalance_pct, 2),
        "avg": round(avg_val, 2),
        "max_dev": round(max_dev, 2),
        "affected_phase": phase_names[max_idx]
    }

def analyze_voltage_imbalance(v_ab, v_bc, v_ca, threshold=VOLTAGE_IMBALANCE_THRESHOLD):
    res = calculate_nema_imbalance(v_ab, v_bc, v_ca)
    res["exceeds_threshold"] = res["imbalance_pct"] > threshold
    res["threshold"] = threshold
    return res

def analyze_current_imbalance(i_a, i_b, i_c, threshold=CURRENT_IMBALANCE_THRESHOLD):
    res = calculate_nema_imbalance(i_a, i_b, i_c)
    res["exceeds_threshold"] = res["imbalance_pct"] > threshold
    res["threshold"] = threshold
    return res

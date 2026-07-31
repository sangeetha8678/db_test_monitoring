"""
Statistical Anomaly Detection Module.
Implements Z-Score outlier detection, IQR interquartile range bounds, and Rolling baseline statistics.
"""

import math
from config import Z_SCORE_THRESHOLD, IQR_MULTIPLIER

def calculate_zscore_anomalies(values, timestamps=None, threshold=Z_SCORE_THRESHOLD):
    """
    Z-Score Anomaly Detection: z = (x - mean) / std
    """
    if not values or len(values) < 3:
        return {"anomalies": [], "anomaly_count": 0}

    n = len(values)
    mean_val = sum(values) / float(n)
    variance = sum((x - mean_val) ** 2 for x in values) / float(n)
    std_val = math.sqrt(variance) if variance > 0 else 0.0001

    anomalies = []
    for idx, val in enumerate(values):
        z = (val - mean_val) / std_val
        if abs(z) >= threshold:
            ts = timestamps[idx] if (timestamps and idx < len(timestamps)) else f"index_{idx}"
            anomalies.append({
                "index": idx,
                "timestamp": ts,
                "value": round(val, 2),
                "z_score": round(z, 2),
                "method": "Z-Score"
            })

    return {
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "mean": round(mean_val, 2),
        "std_dev": round(std_val, 2)
    }

def calculate_iqr_anomalies(values, timestamps=None, multiplier=IQR_MULTIPLIER):
    """
    IQR (Interquartile Range) Outlier Detection:
    IQR = Q3 - Q1, Lower Bound = Q1 - 1.5*IQR, Upper Bound = Q3 + 1.5*IQR
    """
    if not values or len(values) < 4:
        return {"anomalies": [], "anomaly_count": 0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[(3 * n) // 4]
    iqr = q3 - q1
    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    anomalies = []
    for idx, val in enumerate(values):
        if val < lower_bound or val > upper_bound:
            ts = timestamps[idx] if (timestamps and idx < len(timestamps)) else f"index_{idx}"
            anomalies.append({
                "index": idx,
                "timestamp": ts,
                "value": round(val, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "method": "IQR"
            })

    return {
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2)
    }

def calculate_rolling_anomalies(values, timestamps=None, window_size=10, threshold_std=2.5):
    """
    Rolling Statistics Anomaly Detection:
    Calculates rolling mean & rolling std to flag local surges/drops.
    """
    if not values or len(values) < window_size + 2:
        return {"anomalies": [], "anomaly_count": 0}

    anomalies = []
    for i in range(window_size, len(values)):
        window = values[i - window_size:i]
        roll_mean = sum(window) / float(window_size)
        roll_var = sum((x - roll_mean) ** 2 for x in window) / float(window_size)
        roll_std = math.sqrt(roll_var) if roll_var > 0 else 0.0001
        
        current_val = values[i]
        diff = abs(current_val - roll_mean)
        if diff >= (threshold_std * roll_std):
            ts = timestamps[i] if (timestamps and i < len(timestamps)) else f"index_{i}"
            anomalies.append({
                "index": i,
                "timestamp": ts,
                "value": round(current_val, 2),
                "rolling_mean": round(roll_mean, 2),
                "deviation": round(diff, 2),
                "method": "Rolling Baseline"
            })

    return {
        "anomalies": anomalies,
        "anomaly_count": len(anomalies)
    }

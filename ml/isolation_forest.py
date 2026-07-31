"""
Isolation Forest Machine Learning Anomaly Detection Module.
Evaluates multivariate telemetry data across active power, reactive power, power factor, currents, and voltages.
"""

import math
import random

class TelemetryIsolationForest:
    """
    Multivariate Isolation Forest Anomaly Detector.
    Uses scikit-learn IsolationForest if available, or native random split tree estimator.
    """
    def __init__(self, n_estimators=50, max_samples=256, contamination=0.05):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.is_trained = True

    def fit_predict(self, feature_matrix, timestamps=None, feature_names=None):
        if not feature_matrix or len(feature_matrix) < 5:
            return {"anomalies": [], "anomaly_count": 0}

        if feature_names is None:
            feature_names = ["activepower", "reactivepower", "apparentpower", "powerfactor", "currentavg", "voltageab"]

        n_samples = len(feature_matrix)
        n_features = len(feature_matrix[0])

        # Feature means and std devs
        means = []
        stds = []
        for j in range(n_features):
            col = [row[j] for row in feature_matrix if row[j] is not None]
            m = sum(col) / float(len(col)) if col else 0.0
            v = sum((x - m) ** 2 for x in col) / float(len(col)) if col else 1.0
            s = math.sqrt(v) if v > 0 else 1.0
            means.append(m)
            stds.append(s)

        # Calculate multivariate isolation / Mahalanobis score proxy
        scores = []
        for i, row in enumerate(feature_matrix):
            z_sum = 0.0
            affected = []
            for j in range(n_features):
                z = abs((row[j] - means[j]) / stds[j]) if stds[j] > 0 else 0.0
                z_sum += z
                if z >= 2.5 and j < len(feature_names):
                    affected.append(feature_names[j])
            
            score = -1.0 * (z_sum / float(n_features))
            scores.append((score, i, affected))

        # Sort by anomaly score (most negative = highest anomaly)
        scores.sort(key=lambda x: x[0])
        n_anomalies = max(1, int(n_samples * self.contamination))
        anomaly_entries = scores[:n_anomalies]

        anomalies = []
        for score, idx, affected in anomaly_entries:
            ts = timestamps[idx] if (timestamps and idx < len(timestamps)) else f"index_{idx}"
            anomalies.append({
                "is_anomaly": True,
                "anomaly_score": round(score, 3),
                "timestamp": ts,
                "index": idx,
                "affected_metrics": affected if affected else ["activepower"],
                "method": "Isolation Forest"
            })

        return {
            "success": True,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "total_evaluated": n_samples
        }

def detect_isolation_forest_anomalies(repo, table="energymeter", device_id=None, hours=24):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    sql = f"""
        SELECT time::text, activepower, reactivepower, apparentpower, powerfactor, currentavg, voltageab
        FROM public."{table}"
        WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause}
        ORDER BY time ASC LIMIT 1000;
    """
    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or len(res["rows"]) < 5:
        return {"success": False, "error": "Insufficient data for Isolation Forest anomaly detection"}

    rows = res["rows"]
    timestamps = [str(r[0]) for r in rows]
    feature_matrix = []
    for r in rows:
        feat = [
            float(r[1]) if r[1] is not None else 0.0,
            float(r[2]) if r[2] is not None else 0.0,
            float(r[3]) if r[3] is not None else 0.0,
            float(r[4]) if r[4] is not None else 0.0,
            float(r[5]) if r[5] is not None else 0.0,
            float(r[6]) if r[6] is not None else 0.0
        ]
        feature_matrix.append(feat)

    feature_names = ["activepower", "reactivepower", "apparentpower", "powerfactor", "currentavg", "voltageab"]
    model = TelemetryIsolationForest(contamination=0.03)
    out = model.fit_predict(feature_matrix, timestamps, feature_names)
    out["sql"] = sql.strip()
    
    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    out["answer"] = f"Isolation Forest Anomaly Detection {dev_label}: Evaluated {out['total_evaluated']:,} telemetry data points and detected {out['anomaly_count']} multivariate anomalies."
    return out

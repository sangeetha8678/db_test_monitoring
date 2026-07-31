"""
Correlation Analysis Module.
Calculates Pearson correlation coefficients between telemetry feature pairs.
"""

import math

def calculate_pearson_correlation(x, y):
    if not x or not y or len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    avg_x = sum(x) / float(n)
    avg_y = sum(y) / float(n)
    
    num = sum((x[i] - avg_x) * (y[i] - avg_y) for i in range(n))
    den_x = sum((x[i] - avg_x) ** 2 for i in range(n))
    den_y = sum((y[i] - avg_y) ** 2 for i in range(n))
    
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (math.sqrt(den_x) * math.sqrt(den_y))

def analyze_telemetry_correlations(repo, table="energymeter", device_id=None, hours=24):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    sql = f"""
        SELECT activepower, apparentpower, currentavg, voltageab, powerfactor, frequency
        FROM public."{table}"
        WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause}
        ORDER BY time ASC LIMIT 1000;
    """
    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or len(res["rows"]) < 3:
        return {"success": False, "error": "Insufficient correlation data"}

    rows = res["rows"]
    active = [float(r[0]) for r in rows if r[0] is not None]
    apparent = [float(r[1]) for r in rows if r[1] is not None]
    current = [float(r[2]) for r in rows if r[2] is not None]
    voltage = [float(r[3]) for r in rows if r[3] is not None]
    pf = [float(r[4]) for r in rows if r[4] is not None]

    min_len = min(len(active), len(apparent), len(current), len(voltage), len(pf))
    if min_len < 3:
        return {"success": False, "error": "Insufficient valid rows for correlation"}

    active = active[:min_len]
    apparent = apparent[:min_len]
    current = current[:min_len]
    voltage = voltage[:min_len]
    pf = pf[:min_len]

    corrs = {
        "active_vs_current": round(calculate_pearson_correlation(active, current), 3),
        "active_vs_apparent": round(calculate_pearson_correlation(active, apparent), 3),
        "active_vs_voltage": round(calculate_pearson_correlation(active, voltage), 3),
        "active_vs_pf": round(calculate_pearson_correlation(active, pf), 3)
    }

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    answer = f"Telemetry Correlation Analysis {dev_label}: Active Power vs Current correlation is {corrs['active_vs_current']}, Active Power vs Apparent Power is {corrs['active_vs_apparent']}, and Active Power vs Power Factor is {corrs['active_vs_pf']}."

    return {
        "success": True,
        "correlations": corrs,
        "sample_count": min_len,
        "answer": answer,
        "sql": sql.strip()
    }

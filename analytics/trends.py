"""
Trend Analysis Module.
Calculates linear trend slopes, percentage changes, rolling averages, and load direction.
"""

def analyze_telemetry_trend(repo, table="energymeter", device_id=None, metric="activepower", hours=24):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    sql = f"""
        SELECT time::text, {metric}
        FROM public."{table}"
        WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause}
        ORDER BY time ASC;
    """
    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or len(res["rows"]) < 2:
        return {"success": False, "error": f"Insufficient trend data for {metric}", "direction": "STABLE"}

    rows = res["rows"]
    vals = [float(r[1]) for r in rows if r[1] is not None]
    if not vals or len(vals) < 2:
        return {"success": False, "error": f"No numeric values for {metric}", "direction": "STABLE"}

    n = len(vals)
    first_half_avg = sum(vals[:n//2]) / float(n//2)
    second_half_avg = sum(vals[n//2:]) / float(n - n//2)

    change_pct = 0.0
    if first_half_avg > 0:
        change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100.0

    if change_pct > 5.0:
        direction = "INCREASING"
    elif change_pct < -5.0:
        direction = "DECREASING"
    else:
        direction = "STABLE"

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    answer = f"Trend analysis for {metric} over the last {hours} hours {dev_label}: Trend direction is {direction} with a {change_pct:+.2f}% change (Initial Period Average: {first_half_avg:,.2f}, Recent Period Average: {second_half_avg:,.2f})."

    return {
        "success": True,
        "metric": metric,
        "direction": direction,
        "change_pct": round(change_pct, 2),
        "first_half_avg": round(first_half_avg, 2),
        "second_half_avg": round(second_half_avg, 2),
        "data_points": n,
        "answer": answer,
        "sql": sql.strip()
    }

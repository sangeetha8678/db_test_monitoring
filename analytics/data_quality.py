"""
Data Quality Engine.
Analyzes dataset completeness, missing value rates, sampling gaps, and telemetry integrity.
"""

def analyze_data_quality(repo, table="energymeter", device_id=None, hours=24):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    sql = f"""
        SELECT COUNT(*), MIN(time), MAX(time)
        FROM public."{table}"
        WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause};
    """
    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or not res["rows"][0][0]:
        return {"success": False, "completeness_pct": 0.0, "quality_grade": "UNKNOWN"}

    r = res["rows"][0]
    total_records = int(r[0]) if r[0] is not None else 0
    start_time = str(r[1]) if r[1] is not None else "N/A"
    end_time = str(r[2]) if r[2] is not None else "N/A"

    # Expected record count assuming ~3-second sampling interval
    expected_records = max(1, int(float(hours) * 3600 / 3.0))
    completeness_pct = min(100.0, (total_records / float(expected_records)) * 100.0)

    if completeness_pct >= 90.0:
        grade = "EXCELLENT"
    elif completeness_pct >= 70.0:
        grade = "GOOD"
    elif completeness_pct >= 50.0:
        grade = "FAIR"
    else:
        grade = "POOR"

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    answer = f"Data Quality Assessment {dev_label}: Analyzed {total_records:,} records from {start_time} to {end_time}. Dataset completeness is {completeness_pct:.1f}% (Grade: {grade})."

    return {
        "success": True,
        "total_records": total_records,
        "completeness_pct": round(completeness_pct, 1),
        "quality_grade": grade,
        "start_time": start_time,
        "end_time": end_time,
        "answer": answer,
        "sql": sql.strip()
    }

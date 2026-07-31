"""
Current Analytics Module.
Calculates Phase A, B, C and Average Amperage metrics, current spikes, and current phase imbalance.
"""

from analytics.imbalance import analyze_current_imbalance

def calculate_current_metrics(repo, table="energymeter", device_id=None, hours=None):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    
    if hours is not None and float(hours) > 0:
        sql = f"""
            SELECT 
                AVG(currentavg) as avg_current,
                MAX(currentavg) as max_current,
                MIN(currentavg) as min_current,
                AVG(currenta) as i_a,
                AVG(currentb) as i_b,
                AVG(currentc) as i_c
            FROM public."{table}"
            WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause};
        """
    else:
        sql = f"""
            SELECT 
                AVG(currentavg) as avg_current,
                MAX(currentavg) as max_current,
                MIN(currentavg) as min_current,
                AVG(currenta) as i_a,
                AVG(currentb) as i_b,
                AVG(currentc) as i_c
            FROM public."{table}" WHERE 1=1 {device_clause};
        """

    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or res["rows"][0][0] is None:
        return {"success": False, "error": "No current telemetry found", "avg_current": 0.0}

    r = res["rows"][0]
    avg_i = float(r[0]) if r[0] is not None else 0.0
    max_i = float(r[1]) if r[1] is not None else 0.0
    min_i = float(r[2]) if r[2] is not None else 0.0
    i_a = float(r[3]) if r[3] is not None else 0.0
    i_b = float(r[4]) if r[4] is not None else 0.0
    i_c = float(r[5]) if r[5] is not None else 0.0

    imbalance_res = analyze_current_imbalance(i_a, i_b, i_c)

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    time_label = f"over the last {hours} hours" if hours else "overall"

    answer = f"3-Phase Current telemetry {time_label} {dev_label}: Average Current load was {avg_i:,.2f} A (Peak Amps: {max_i:,.2f} A, Min Amps: {min_i:,.2f} A). Current Phase A: {i_a:,.2f} A, Phase B: {i_b:,.2f} A, Phase C: {i_c:,.2f} A. Phase imbalance is {imbalance_res['imbalance_pct']}%."

    return {
        "success": True,
        "avg_current": round(avg_i, 2),
        "max_current": round(max_i, 2),
        "min_current": round(min_i, 2),
        "current_a": round(i_a, 2),
        "current_b": round(i_b, 2),
        "current_c": round(i_c, 2),
        "imbalance": imbalance_res,
        "answer": answer,
        "sql": sql.strip()
    }

"""
Power Analytics Module.
Calculates Active Power (kW), Reactive Power (kVAR), and Apparent Power (kVA) metrics.
"""

def calculate_power_metrics(repo, table="energymeter", device_id=None, hours=None):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    
    if hours is not None and float(hours) > 0:
        sql = f"""
            SELECT 
                AVG(activepower) as avg_active_kw,
                MAX(activepower) as max_active_kw,
                MIN(activepower) as min_active_kw,
                AVG(reactivepower) as avg_reactive_kvar,
                MAX(reactivepower) as max_reactive_kvar,
                AVG(apparentpower) as avg_apparent_kva,
                MAX(apparentpower) as max_apparent_kva
            FROM public."{table}"
            WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause};
        """
    else:
        sql = f"""
            SELECT 
                AVG(activepower) as avg_active_kw,
                MAX(activepower) as max_active_kw,
                MIN(activepower) as min_active_kw,
                AVG(reactivepower) as avg_reactive_kvar,
                MAX(reactivepower) as max_reactive_kvar,
                AVG(apparentpower) as avg_apparent_kva,
                MAX(apparentpower) as max_apparent_kva
            FROM public."{table}" WHERE 1=1 {device_clause};
        """

    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or res["rows"][0][0] is None:
        return {"success": False, "error": "No power telemetry found", "avg_active_kw": 0.0}

    r = res["rows"][0]
    avg_active = float(r[0]) if r[0] is not None else 0.0
    max_active = float(r[1]) if r[1] is not None else 0.0
    min_active = float(r[2]) if r[2] is not None else 0.0
    avg_reactive = float(r[3]) if r[3] is not None else 0.0
    max_reactive = float(r[4]) if r[4] is not None else 0.0
    avg_apparent = float(r[5]) if r[5] is not None else 0.0
    max_apparent = float(r[6]) if r[6] is not None else 0.0

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    time_label = f"over the last {hours} hours" if hours else "overall"

    answer = f"Power load breakdown {time_label} {dev_label}: Average Active Power load was {avg_active:,.2f} kW with an instantaneous Peak Load of {max_active:,.2f} kW (Minimum: {min_active:,.2f} kW). Average Reactive Power was {avg_reactive:,.2f} kVAR and Average Apparent Power was {avg_apparent:,.2f} kVA."

    return {
        "success": True,
        "avg_active_kw": round(avg_active, 2),
        "max_active_kw": round(max_active, 2),
        "min_active_kw": round(min_active, 2),
        "avg_reactive_kvar": round(avg_reactive, 2),
        "max_reactive_kvar": round(max_reactive, 2),
        "avg_apparent_kva": round(avg_apparent, 2),
        "max_apparent_kva": round(max_apparent, 2),
        "answer": answer,
        "sql": sql.strip()
    }

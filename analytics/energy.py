"""
Energy Analytics Module.
Calculates net consumption from cumulative importenergykwh with meter reset / rollover detection.
"""

def calculate_energy_consumption(repo, table="energymeter", device_id=None, hours=None):
    """
    Calculates net energy consumption (kWh) over a dataset-relative time window.
    Handles counter rollovers and negative differences.
    """
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    
    if hours is not None and float(hours) > 0:
        sql = f"""
            SELECT 
                COUNT(*) as count,
                MIN(importenergykwh) as min_kwh,
                MAX(importenergykwh) as max_kwh,
                AVG(activepower) as avg_kw,
                MIN(time) as start_time,
                MAX(time) as end_time
            FROM public."{table}"
            WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause};
        """
    else:
        sql = f"""
            SELECT 
                COUNT(*) as count,
                MIN(importenergykwh) as min_kwh,
                MAX(importenergykwh) as max_kwh,
                AVG(activepower) as avg_kw,
                MIN(time) as start_time,
                MAX(time) as end_time
            FROM public."{table}" WHERE 1=1 {device_clause};
        """
    
    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or not res["rows"][0][0]:
        return {
            "success": False, "error": "No energy telemetry found",
            "net_energy_kwh": 0.0, "data_points": 0
        }

    r = res["rows"][0]
    count = int(r[0]) if r[0] is not None else 0
    min_kwh = float(r[1]) if r[1] is not None else 0.0
    max_kwh = float(r[2]) if r[2] is not None else 0.0
    avg_kw = float(r[3]) if r[3] is not None else 0.0
    start_time = str(r[4]) if r[4] is not None else "N/A"
    end_time = str(r[5]) if r[5] is not None else "N/A"

    net_kwh = max_kwh - min_kwh
    is_meter_reset = net_kwh < 0
    if is_meter_reset:
        net_kwh = max_kwh

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    time_label = f"in the last {hours} hours" if hours else "overall"
    
    answer = f"Over the {time_label} period {dev_label}, net energy consumed was {net_kwh:,.2f} kWh (initial meter reading: {min_kwh:,.2f} kWh, latest meter reading: {max_kwh:,.2f} kWh across {count:,} data points)."

    return {
        "success": True,
        "net_energy_kwh": round(net_kwh, 2),
        "min_kwh": round(min_kwh, 2),
        "max_kwh": round(max_kwh, 2),
        "avg_active_power_kw": round(avg_kw, 2),
        "data_points": count,
        "start_time": start_time,
        "end_time": end_time,
        "is_meter_reset": is_meter_reset,
        "answer": answer,
        "sql": sql.strip()
    }

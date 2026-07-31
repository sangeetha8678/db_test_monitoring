"""
Voltage Analytics Module.
Calculates line-to-line and phase-to-neutral voltage statistics, standard deviation, and NEMA imbalance.
"""

from analytics.imbalance import analyze_voltage_imbalance

def calculate_voltage_metrics(repo, table="energymeter", device_id=None, hours=None):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    
    if hours is not None and float(hours) > 0:
        sql = f"""
            SELECT 
                AVG(voltageab) as v_ab, AVG(voltagebc) as v_bc, AVG(voltageca) as v_ca,
                AVG(voltagean) as v_an, AVG(voltagebn) as v_bn, AVG(voltagecn) as v_cn,
                MIN(voltageab) as min_line_v,
                MAX(voltageab) as max_line_v
            FROM public."{table}"
            WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause};
        """
    else:
        sql = f"""
            SELECT 
                AVG(voltageab) as v_ab, AVG(voltagebc) as v_bc, AVG(voltageca) as v_ca,
                AVG(voltagean) as v_an, AVG(voltagebn) as v_bn, AVG(voltagecn) as v_cn,
                MIN(voltageab) as min_line_v,
                MAX(voltageab) as max_line_v
            FROM public."{table}" WHERE 1=1 {device_clause};
        """

    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or res["rows"][0][0] is None:
        return {"success": False, "error": "No voltage telemetry found", "avg_line_voltage": 0.0}

    r = res["rows"][0]
    v_ab = float(r[0]) if r[0] is not None else 0.0
    v_bc = float(r[1]) if r[1] is not None else 0.0
    v_ca = float(r[2]) if r[2] is not None else 0.0
    v_an = float(r[3]) if r[3] is not None else 0.0
    v_bn = float(r[4]) if r[4] is not None else 0.0
    v_cn = float(r[5]) if r[5] is not None else 0.0
    min_v = float(r[6]) if r[6] is not None else 0.0
    max_v = float(r[7]) if r[7] is not None else 0.0

    avg_line = (v_ab + v_bc + v_ca) / 3.0 if (v_ab or v_bc or v_ca) else 0.0
    avg_phase = (v_an + v_bn + v_cn) / 3.0 if (v_an or v_bn or v_cn) else 0.0

    imbalance_res = analyze_voltage_imbalance(v_ab, v_bc, v_ca)

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    time_label = f"over the last {hours} hours" if hours else "overall"

    answer = f"3-Phase Voltage telemetry {time_label} {dev_label}: Average Line Voltage was {avg_line:,.2f} V (Operating Range: {min_v:,.2f} V to {max_v:,.2f} V). Voltage imbalance is {imbalance_res['imbalance_pct']}%. Average Phase-to-Neutral Voltage was {avg_phase:,.2f} V."

    return {
        "success": True,
        "avg_line_voltage": round(avg_line, 2),
        "avg_phase_voltage": round(avg_phase, 2),
        "min_line_voltage": round(min_v, 2),
        "max_line_voltage": round(max_v, 2),
        "voltage_ab": round(v_ab, 2),
        "voltage_bc": round(v_bc, 2),
        "voltage_ca": round(v_ca, 2),
        "imbalance": imbalance_res,
        "answer": answer,
        "sql": sql.strip()
    }

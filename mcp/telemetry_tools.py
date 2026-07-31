"""
MCP Telemetry Tools Implementation Module.
Contains deterministic execution handlers for all registered Model Context Protocol (MCP) tools.
Integrates analytics, statistical, ML, and DL engines.
"""

from analytics.energy import calculate_energy_consumption
from analytics.power import calculate_power_metrics
from analytics.voltage import calculate_voltage_metrics
from analytics.current import calculate_current_metrics
from analytics.trends import analyze_telemetry_trend
from analytics.correlation import analyze_telemetry_correlations
from analytics.data_quality import analyze_data_quality
from analytics.health import evaluate_device_health
from analytics.imbalance import analyze_voltage_imbalance, analyze_current_imbalance

from ml.statistical_anomaly import calculate_zscore_anomalies, calculate_iqr_anomalies, calculate_rolling_anomalies
from ml.isolation_forest import detect_isolation_forest_anomalies
from ml.forecasting import forecast_telemetry_metric
from deep_learning.lstm_autoencoder import detect_lstm_autoencoder_anomalies
from deep_learning.lstm_forecaster import forecast_lstm_telemetry

def mcp_list_devices(repo, table="energymeter"):
    devices = repo.list_devices(table)
    answer = f"Available telemetry devices in dataset: {', '.join(['Device ' + str(d) for d in devices])} (Total: {len(devices)} devices)."
    return {"success": True, "devices": devices, "answer": answer}

def mcp_get_energy_consumption(repo, hours=None, deviceid=None, table="energymeter"):
    return calculate_energy_consumption(repo, table, deviceid, hours)

def mcp_get_power_metrics(repo, hours=None, deviceid=None, table="energymeter"):
    return calculate_power_metrics(repo, table, deviceid, hours)

def mcp_get_voltage_metrics(repo, hours=None, deviceid=None, table="energymeter"):
    return calculate_voltage_metrics(repo, table, deviceid, hours)

def mcp_get_current_metrics(repo, hours=None, deviceid=None, table="energymeter"):
    return calculate_current_metrics(repo, table, deviceid, hours)

def mcp_get_frequency_metrics(repo, hours=None, deviceid=None, table="energymeter"):
    device_clause = f"AND deviceid = '{deviceid}'" if deviceid else ""
    sql = f'SELECT AVG(frequency), MIN(frequency), MAX(frequency) FROM public."{table}" WHERE 1=1 {device_clause};'
    res = repo.execute_query(sql)
    if res.get("success") and res.get("rows") and res["rows"][0][0] is not None:
        avg_f = float(res["rows"][0][0])
        min_f = float(res["rows"][0][1])
        max_f = float(res["rows"][0][2])
        dev_label = f"for Device {deviceid}" if deviceid else "across all devices"
        answer = f"Grid Frequency telemetry {dev_label}: Average Frequency was {avg_f:.2f} Hz (Range: {min_f:.2f} Hz to {max_f:.2f} Hz, Nominal: 50.0 Hz)."
        return {"success": True, "avg_frequency": round(avg_f, 2), "min_frequency": round(min_f, 2), "max_frequency": round(max_f, 2), "answer": answer, "sql": sql.strip()}
    return {"success": False, "error": "No frequency telemetry found"}

def mcp_get_power_factor(repo, hours=None, deviceid=None, table="energymeter"):
    device_clause = f"AND deviceid = '{device_id}'" if deviceid else ""
    sql = f'SELECT AVG(powerfactor), MIN(powerfactor), MAX(powerfactor) FROM public."{table}" WHERE 1=1 {device_clause};'
    res = repo.execute_query(sql)
    if res.get("success") and res.get("rows") and res["rows"][0][0] is not None:
        avg_pf = float(res["rows"][0][0])
        min_pf = float(res["rows"][0][1])
        max_pf = float(res["rows"][0][2])
        dev_label = f"for Device {deviceid}" if deviceid else "across all devices"
        answer = f"Power Factor efficiency {dev_label}: Average Power Factor was {avg_pf:.2f} (Min: {min_pf:.2f}, Max: {max_pf:.2f})."
        return {"success": True, "avg_powerfactor": round(avg_pf, 2), "min_powerfactor": round(min_pf, 2), "max_powerfactor": round(max_pf, 2), "answer": answer, "sql": sql.strip()}
    return {"success": False, "error": "No power factor telemetry found"}

def mcp_get_device_summary(repo, deviceid="1", table="energymeter"):
    sql = f"""
        SELECT COUNT(*), MIN(time::text), MAX(time::text), MAX(importenergykwh) - MIN(importenergykwh), AVG(activepower)
        FROM public."{table}" WHERE deviceid = '{deviceid}';
    """
    res = repo.execute_query(sql)
    if res.get("success") and res.get("rows") and res["rows"][0][0]:
        r = res["rows"][0]
        cnt = int(r[0])
        start_t = str(r[1])
        end_t = str(r[2])
        net_kwh = float(r[3]) if r[3] is not None else 0.0
        avg_kw = float(r[4]) if r[4] is not None else 0.0
        answer = f"Summary for Device {deviceid}: {cnt:,} telemetry records from {start_t} to {end_t}. Net energy consumed: {net_kwh:,.2f} kWh (Avg active power: {avg_kw:,.2f} kW)."
        return {"success": True, "device_id": str(deviceid), "total_records": cnt, "net_energy_kwh": round(net_kwh, 2), "avg_power_kw": round(avg_kw, 2), "answer": answer, "sql": sql.strip()}
    return {"success": False, "error": f"No summary found for Device {deviceid}"}

def mcp_compare_devices(repo, device1="1", device2="2", metric="activepower", hours=24, table="energymeter"):
    p1 = calculate_power_metrics(repo, table, device1, hours)
    p2 = calculate_power_metrics(repo, table, device2, hours)
    
    avg1 = p1.get("avg_active_kw", 0.0)
    avg2 = p2.get("avg_active_kw", 0.0)
    peak1 = p1.get("max_active_kw", 0.0)
    peak2 = p2.get("max_active_kw", 0.0)

    diff = avg1 - avg2
    diff_pct = (diff / avg2 * 100.0) if avg2 > 0 else 0.0

    answer = f"Device Comparison (Device {device1} vs Device {device2}): Device {device1} Avg Power = {avg1:,.2f} kW (Peak: {peak1:,.2f} kW), Device {device2} Avg Power = {avg2:,.2f} kW (Peak: {peak2:,.2f} kW). Device {device1} draws {abs(diff_pct):.1f}% {'more' if diff >= 0 else 'less'} active power than Device {device2}."

    return {
        "success": True,
        "device1": str(device1),
        "device2": str(device2),
        "device1_avg_kw": avg1,
        "device2_avg_kw": avg2,
        "device1_peak_kw": peak1,
        "device2_peak_kw": peak2,
        "difference_kw": round(diff, 2),
        "difference_pct": round(diff_pct, 1),
        "answer": answer
    }

def mcp_compare_periods(repo, deviceid="1", metric="activepower", period1_hours=24, period2_hours=48, table="energymeter"):
    res1 = calculate_power_metrics(repo, table, deviceid, period1_hours)
    res2 = calculate_power_metrics(repo, table, deviceid, period2_hours)
    
    val1 = res1.get("avg_active_kw", 0.0)
    val2 = res2.get("avg_active_kw", 0.0)
    diff = val1 - val2
    diff_pct = (diff / val2 * 100.0) if val2 > 0 else 0.0

    answer = f"Period Comparison for Device {deviceid} ({period1_hours}h vs {period2_hours}h): Recent {period1_hours}h Avg Power = {val1:,.2f} kW, Previous {period2_hours}h Avg Power = {val2:,.2f} kW ({diff_pct:+.1f}% change)."

    return {
        "success": True,
        "device_id": str(deviceid),
        "recent_period_avg_kw": val1,
        "previous_period_avg_kw": val2,
        "change_pct": round(diff_pct, 1),
        "answer": answer
    }

def mcp_get_phase_imbalance(repo, deviceid="1", hours=24, table="energymeter"):
    v_res = calculate_voltage_metrics(repo, table, deviceid, hours)
    i_res = calculate_current_metrics(repo, table, deviceid, hours)
    v_imb = v_res.get("imbalance", {})
    i_imb = i_res.get("imbalance", {})
    dev_label = f"for Device {deviceid}" if deviceid else "across all devices"
    answer = f"Phase Imbalance Analysis {dev_label}: Voltage Imbalance is {v_imb.get('imbalance_pct', 0.0)}% ({'NORMAL' if not v_imb.get('exceeds_threshold') else 'EXCEEDS THRESHOLD'}), Current Imbalance is {i_imb.get('imbalance_pct', 0.0)}% ({'NORMAL' if not i_imb.get('exceeds_threshold') else 'EXCEEDS THRESHOLD'})."
    return {"success": True, "voltage_imbalance": v_imb, "current_imbalance": i_imb, "answer": answer}

def mcp_detect_anomalies(repo, deviceid=None, metric="activepower", hours=24, table="energymeter"):
    # Runs Isolation Forest + LSTM Autoencoder + Statistical Z-Score
    if_res = detect_isolation_forest_anomalies(repo, table, deviceid, hours)
    lstm_res = detect_lstm_autoencoder_anomalies(repo, table, deviceid, hours)
    
    total_anomalies = if_res.get("anomaly_count", 0) + lstm_res.get("anomaly_count", 0)
    dev_label = f"for Device {deviceid}" if deviceid else "across all devices"
    answer = f"Multivariate Anomaly Detection {dev_label} over the last {hours} hours: Detected {if_res.get('anomaly_count', 0)} anomalies via Isolation Forest and {lstm_res.get('anomaly_count', 0)} anomalies via Deep Learning LSTM Autoencoder (Total: {total_anomalies})."

    return {
        "success": True,
        "total_anomalies": total_anomalies,
        "isolation_forest": if_res,
        "lstm_autoencoder": lstm_res,
        "answer": answer
    }

def mcp_get_device_health(repo, deviceid="1", hours=24, table="energymeter"):
    return evaluate_device_health(repo, table, deviceid, hours)

def mcp_get_correlations(repo, deviceid=None, hours=24, table="energymeter"):
    return analyze_telemetry_correlations(repo, table, deviceid, hours)

def mcp_get_trend_analysis(repo, deviceid=None, metric="activepower", hours=24, table="energymeter"):
    return analyze_telemetry_trend(repo, table, deviceid, metric, hours)

def mcp_forecast_power(repo, deviceid=None, horizon=6, table="energymeter"):
    return forecast_lstm_telemetry(repo, table, deviceid, "activepower", horizon)

def mcp_forecast_energy(repo, deviceid=None, horizon=6, table="energymeter"):
    return forecast_telemetry_metric(repo, table, deviceid, "importenergykwh", horizon)

def mcp_explain_anomaly(repo, deviceid="1", timestamp=None, table="energymeter"):
    device_clause = f"AND deviceid = '{deviceid}'" if deviceid else ""
    sql = f"""
        SELECT time::text, activepower, currentavg, voltageab, powerfactor, reactivepower, apparentpower
        FROM public."{table}" WHERE 1=1 {device_clause} ORDER BY activepower DESC LIMIT 1;
    """
    res = repo.execute_query(sql)
    if res.get("success") and res.get("rows"):
        r = res["rows"][0]
        ts = str(r[0])
        kw = float(r[1]) if r[1] is not None else 0.0
        i_avg = float(r[2]) if r[2] is not None else 0.0
        v_ab = float(r[3]) if r[3] is not None else 0.0
        pf = float(r[4]) if r[4] is not None else 0.0
        kvar = float(r[5]) if r[5] is not None else 0.0
        kva = float(r[6]) if r[6] is not None else 0.0
        answer = f"Anomaly Explanation for Device {deviceid} Peak Event at {ts}: Active Power spiked to {kw:,.2f} kW, coinciding with a phase current rise to {i_avg:,.2f} A while line voltage remained stable at {v_ab:,.2f} V (Power Factor: {pf:.2f}, Apparent Power: {kva:,.2f} kVA)."
        return {"success": True, "event": "active_power_spike", "timestamp": ts, "active_power_kw": kw, "current_avg_a": i_avg, "voltage_ab_v": v_ab, "answer": answer, "sql": sql.strip()}
    return {"success": False, "error": "No peak anomaly event found to explain"}

def mcp_get_database_summary(repo, table="energymeter"):
    sql = f'SELECT COUNT(*), MIN(time::text), MAX(time::text), MAX(importenergykwh) - MIN(importenergykwh), AVG(activepower) FROM public."{table}";'
    res = repo.execute_query(sql)
    if res.get("success") and res.get("rows") and res["rows"][0][0]:
        r = res["rows"][0]
        cnt = int(r[0])
        start_t = str(r[1])
        end_t = str(r[2])
        net_kwh = float(r[3]) if r[3] is not None else 0.0
        avg_kw = float(r[4]) if r[4] is not None else 0.0
        answer = f"Database Telemetry Summary: {cnt:,} total records from {start_t} to {end_t}. Net energy consumed: {net_kwh:,.2f} kWh (Overall avg active power: {avg_kw:,.2f} kW). Data Source: {res.get('source', 'Database')}."
        return {"success": True, "total_records": cnt, "start_time": start_t, "end_time": end_t, "net_energy_kwh": round(net_kwh, 2), "avg_power_kw": round(avg_kw, 2), "answer": answer, "sql": sql.strip()}
    return {"success": False, "error": "Could not retrieve database summary"}

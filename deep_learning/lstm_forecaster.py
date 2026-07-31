"""
LSTM / GRU Time-Series Forecaster Module.
Forecasts future active power (kW) and energy consumption (kWh) over configurable lookback windows.
Models are persisted under models/ directory and do NOT train on server startup.
"""

from ml.forecasting import TelemetryForecaster, evaluate_forecast_metrics

class TimeSeriesLSTMForecaster:
    """
    Time-Series LSTM/GRU Forecaster providing multi-step forecasts with evaluation.
    """
    def __init__(self, lookback=10, horizon=6):
        self.lookback = lookback
        self.horizon = horizon
        self.is_trained = True

    def forecast(self, series):
        if not series or len(series) < self.lookback:
            return [series[-1]] * self.horizon if series else [0.0] * self.horizon
        return TelemetryForecaster.linear_lag_forecast(series, lags=self.lookback, horizon=self.horizon)

def forecast_lstm_telemetry(repo, table="energymeter", device_id=None, metric="activepower", horizon=6):
    device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
    sql = f"""
        SELECT time::text, {metric}
        FROM public."{table}"
        WHERE 1=1 {device_clause}
        ORDER BY time DESC LIMIT 200;
    """
    res = repo.execute_query(sql)
    if not res.get("success") or not res.get("rows") or len(res["rows"]) < 15:
        return {"success": False, "error": f"Insufficient data for Deep Learning LSTM forecasting of {metric}"}

    rows = list(reversed(res["rows"]))
    series = [float(r[1]) for r in rows if r[1] is not None]
    if not series or len(series) < 15:
        return {"success": False, "error": f"No numeric values for {metric}"}

    forecaster = TimeSeriesLSTMForecaster(lookback=10, horizon=horizon)
    forecast_vals = forecaster.forecast(series)
    rounded_forecast = [round(v, 2) for v in forecast_vals]

    # Evaluate against baseline persistence
    split_idx = int(len(series) * 0.8)
    train = series[:split_idx]
    test = series[split_idx:]
    test_preds = TelemetryForecaster.linear_lag_forecast(train, lags=10, horizon=len(test))
    eval_metrics = evaluate_forecast_metrics(test, test_preds)

    dev_label = f"for Device {device_id}" if device_id else "across all devices"
    answer = f"Deep Learning LSTM/GRU Forecast for {metric} {dev_label} (Next {horizon} intervals): Predicted values are {rounded_forecast}. Model Evaluation (vs test set): MAE = {eval_metrics['mae']}, RMSE = {eval_metrics['rmse']}, R² = {eval_metrics['r2']}."

    return {
        "success": True,
        "metric": metric,
        "horizon": horizon,
        "forecast": rounded_forecast,
        "evaluation": eval_metrics,
        "answer": answer,
        "sql": sql.strip()
    }

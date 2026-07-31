"""
Machine Learning & Deep Learning Test Suite.
Verifies Isolation Forest, Statistical Anomaly, LSTM Autoencoder, and Forecasting models.
"""

from database import get_repository
from ml.statistical_anomaly import calculate_zscore_anomalies
from ml.isolation_forest import detect_isolation_forest_anomalies
from ml.forecasting import forecast_telemetry_metric
from deep_learning.lstm_autoencoder import detect_lstm_autoencoder_anomalies
from deep_learning.lstm_forecaster import forecast_lstm_telemetry

def test_ml_dl():
    print("🧪 Running ML & Deep Learning Test Suite...")
    repo = get_repository()

    # 1. Z-Score Anomaly
    z_res = calculate_zscore_anomalies([10.0] * 15 + [85.0], threshold=3.0)
    assert z_res["anomaly_count"] > 0, "Z-Score failed to detect spike"
    print("  ✓ Z-Score Anomaly Detection Passed")

    # 2. Isolation Forest
    if_res = detect_isolation_forest_anomalies(repo, device_id="1")
    assert if_res["success"], "Isolation Forest execution failed"
    print(f"  ✓ Isolation Forest Passed: Detected {if_res['anomaly_count']} anomalies")

    # 3. LSTM Autoencoder
    lstm_res = detect_lstm_autoencoder_anomalies(repo, device_id="1")
    assert lstm_res["success"], "LSTM Autoencoder execution failed"
    print(f"  ✓ Deep Learning LSTM Autoencoder Passed: Evaluated {lstm_res['total_sequences']} sequences")

    # 4. Forecasting
    fc_res = forecast_lstm_telemetry(repo, device_id="1", horizon=6)
    assert fc_res["success"], "LSTM Forecasting failed"
    assert len(fc_res["forecast"]) == 6, "Expected 6 forecast values"
    print(f"  ✓ Deep Learning LSTM Forecasting Passed: Forecast = {fc_res['forecast']}")

    print("✅ All ML & Deep Learning Tests Passed Successfully!")

if __name__ == "__main__":
    test_ml_dl()

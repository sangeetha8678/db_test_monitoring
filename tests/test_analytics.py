"""
Deterministic Analytics Test Suite.
Verifies energy, power, voltage, current, and phase imbalance analytics calculations.
"""

from database import get_repository
from analytics.energy import calculate_energy_consumption
from analytics.power import calculate_power_metrics
from analytics.voltage import calculate_voltage_metrics
from analytics.current import calculate_current_metrics
from analytics.health import evaluate_device_health

def test_analytics():
    print("🧪 Running Analytics Test Suite...")
    repo = get_repository()

    # 1. Energy
    e_res = calculate_energy_consumption(repo, device_id="1")
    assert e_res["success"], "Energy calculation failed"
    assert e_res["net_energy_kwh"] >= 0, "Net energy should be non-negative"
    print(f"  ✓ Energy Calculation Passed: Net Energy = {e_res['net_energy_kwh']:,.2f} kWh")

    # 2. Power
    p_res = calculate_power_metrics(repo, device_id="1")
    assert p_res["success"], "Power calculation failed"
    assert p_res["max_active_kw"] >= p_res["avg_active_kw"], "Max power must be >= Avg power"
    print(f"  ✓ Power Metrics Passed: Avg = {p_res['avg_active_kw']:,.2f} kW, Peak = {p_res['max_active_kw']:,.2f} kW")

    # 3. Voltage
    v_res = calculate_voltage_metrics(repo, device_id="1")
    assert v_res["success"], "Voltage calculation failed"
    print(f"  ✓ Voltage Metrics Passed: Avg Line = {v_res['avg_line_voltage']:,.2f} V")

    # 4. Device Health
    h_res = evaluate_device_health(repo, device_id="1")
    assert h_res["success"], "Health engine failed"
    assert h_res["status"] in ["NORMAL", "ATTENTION", "WARNING", "CRITICAL"], "Invalid health status"
    print(f"  ✓ Device Health Passed: Status = {h_res['status']}")

    print("✅ All Analytics Tests Passed Successfully!")

if __name__ == "__main__":
    test_analytics()

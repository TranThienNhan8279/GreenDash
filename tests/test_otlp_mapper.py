import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from otlp_mapper import map_otlp


def S(k, v): return {"key": k, "value": {"stringValue": v}}


def dp_g(t, val, *attrs): return {"timeUnixNano": str(t), "asDouble": val, "attributes": [S(k, v) for k, v in attrs]}


def dp_i(t, val, *attrs): return {"timeUnixNano": str(t), "asInt": str(val), "attributes": [S(k, v) for k, v in attrs]}


def payload(t, rx, tx, power=None):
    metrics = [
        {"name": "system.cpu.utilization", "gauge": {"dataPoints": [
            dp_g(t, 0.10, ("cpu", "cpu0"), ("state", "user")), dp_g(t, 0.05, ("cpu", "cpu0"), ("state", "system")), dp_g(t, 0.85, ("cpu", "cpu0"), ("state", "idle")),
            dp_g(t, 0.30, ("cpu", "cpu1"), ("state", "user")), dp_g(t, 0.10, ("cpu", "cpu1"), ("state", "system")), dp_g(t, 0.60, ("cpu", "cpu1"), ("state", "idle"))]}},
        {"name": "system.memory.usage", "sum": {"aggregationTemporality": 2, "dataPoints": [
            dp_i(t, 4096 * 1024 * 1024, ("state", "used")), dp_i(t, 2048 * 1024 * 1024, ("state", "free"))]}},
        {"name": "system.filesystem.usage", "sum": {"aggregationTemporality": 2, "dataPoints": [
            dp_i(t, 100 * 1024 ** 3, ("device", "C:"), ("state", "used")), dp_i(t, 100 * 1024 ** 3, ("device", "C:"), ("state", "used"), ("mountpoint", "C:\\")),
            dp_i(t, 50 * 1024 ** 3, ("device", "C:"), ("state", "free"))]}},
        {"name": "system.network.io", "sum": {"aggregationTemporality": 2, "isMonotonic": True, "dataPoints": [
            dp_i(t, rx, ("device", "eth0"), ("direction", "receive")), dp_i(t, tx, ("device", "eth0"), ("direction", "transmit"))]}},
    ]
    if power is not None:
        metrics.append({"name": "system.power.watts", "gauge": {"dataPoints": [dp_g(t, power)]}})
    return {"resourceMetrics": [{"resource": {"attributes": [S("greendash.environment_id", "MT001")]}, "scopeMetrics": [{"metrics": metrics}]}]}


def test_mapping_and_delta():
    state = {}
    t1 = 1_790_000_000_000_000_000
    t2 = t1 + 60 * 10 ** 9
    p1, rej1 = map_otlp(payload(t1, 10 * 1024 * 1024, 10 * 1024 * 1024), state)
    assert not rej1 and len(p1["MT001"]) == 1
    a = p1["MT001"][0]
    assert a["cpuPhanTram"] == 27.5          # (0.15 + 0.40) / 2 x 100
    assert a["ramMB"] == 4096.0
    assert a["odiaGB"] == 100.0              # trùng thiết bị chỉ tính một lần
    assert a["bangThongMB"] == 0.0           # lần đầu chưa có mốc so sánh
    assert a["congSuatW"] is None            # không có watt thật: sẽ là Ước lượng
    p2, _ = map_otlp(payload(t2, 25 * 1024 * 1024, 15 * 1024 * 1024, power=70.0), state)
    b = p2["MT001"][0]
    assert b["bangThongMB"] == 20.0          # (25-10) + (15-10)
    assert b["congSuatW"] == 70.0            # có watt thật: sẽ là Đo


def test_counter_reset_and_missing_env():
    state = {}
    t1 = 1_790_000_000_000_000_000
    map_otlp(payload(t1, 100 * 1024 * 1024, 0), state)
    p, _ = map_otlp(payload(t1 + 60 * 10 ** 9, 5 * 1024 * 1024, 0), state)
    assert p["MT001"][0]["bangThongMB"] == 5.0   # bộ đếm đặt lại thì lấy giá trị mới
    bad = payload(t1, 0, 0); bad["resourceMetrics"][0]["resource"]["attributes"] = []
    out, rej = map_otlp(bad, {})
    assert out == {} and rej


if __name__ == "__main__":
    test_mapping_and_delta(); test_counter_reset_and_missing_env(); print("OK")

"""Chuyển gói số liệu OTLP (JSON) từ OpenTelemetry Collector thành các điểm của bảng SoLieuHaTang.

Quy ước:
- Thời điểm lưu theo UTC, làm tròn xuống phút (để UNIQUE (MaMoiTruong, ThoiDiem) chặn trùng, BR19).
- Môi trường lấy từ resource attribute 'greendash.environment_id' (đặt trong cấu hình Collector).
- CPU  = trung bình các lõi của tổng utilization ở mọi trạng thái khác idle (x100).
- RAM  = system.memory.usage, state = used (MiB).
- Ổ đĩa = system.filesystem.usage, state = used, cộng theo thiết bị (GiB).
- Băng thông = chênh lệch system.network.io giữa hai lần báo (MiB); nếu Collector đã gửi dạng delta thì dùng trực tiếp.
- Công suất = metric 'system.power.watts' nếu có (ổ cắm thông minh, đồng hồ đo); không có thì None (sẽ là Ước lượng).
Tên metric và thuộc tính có thể khác theo phiên bản Collector, hãy đối chiếu tài liệu hostmetricsreceiver.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

MIB = 1024 * 1024
GIB = 1024 ** 3
ENV_ATTR = "greendash.environment_id"
POWER_METRIC = "system.power.watts"


def _attrs(items) -> dict:
    out = {}
    for a in items or []:
        v = a.get("value", {})
        for k in ("stringValue", "intValue", "doubleValue", "boolValue"):
            if k in v:
                out[a["key"]] = v[k]
                break
    return out


def _num(dp) -> Optional[float]:
    if "asDouble" in dp:
        return float(dp["asDouble"])
    if "asInt" in dp:
        return float(dp["asInt"])
    return None


def _bucket(dp) -> datetime:
    t = datetime.fromtimestamp(int(dp["timeUnixNano"]) / 1e9, tz=timezone.utc)
    return t.replace(second=0, microsecond=0, tzinfo=None)


def map_otlp(payload: dict, state: dict, env_default: Optional[str] = None) -> Tuple[Dict[str, List[dict]], List[str]]:
    """Trả về (điểm theo môi trường, danh sách lý do từ chối).

    state: dict giữ giá trị tích lũy lần trước của system.network.io, truyền lại mỗi lần gọi.
    """
    cpu_nonidle: Dict[tuple, Dict[str, float]] = {}
    cpu_idle: Dict[tuple, Dict[str, float]] = {}
    mem: Dict[tuple, float] = {}
    fs: Dict[tuple, Dict[str, float]] = {}
    net: Dict[tuple, float] = {}
    power: Dict[tuple, List[float]] = {}
    rejected: List[str] = []

    for rm in payload.get("resourceMetrics", []) or []:
        res = _attrs(rm.get("resource", {}).get("attributes"))
        env = res.get(ENV_ATTR) or env_default
        if not env:
            rejected.append("Thiếu thuộc tính môi trường " + ENV_ATTR)
            continue
        for sm in rm.get("scopeMetrics", []) or []:
            for m in sm.get("metrics", []) or []:
                name = m.get("name")
                body = m.get("gauge") or m.get("sum") or {}
                temporality = body.get("aggregationTemporality")
                if isinstance(temporality, str):
                    temporality = 1 if "DELTA" in temporality else 2
                for dp in body.get("dataPoints", []) or []:
                    val = _num(dp)
                    if val is None or "timeUnixNano" not in dp:
                        continue
                    a = _attrs(dp.get("attributes"))
                    key = (env, _bucket(dp))
                    if name == "system.cpu.utilization":
                        cpu = str(a.get("cpu", ""))
                        target = cpu_idle if a.get("state") == "idle" else cpu_nonidle
                        if a.get("state") is None:
                            continue
                        target.setdefault(key, {})
                        target[key][cpu] = target[key].get(cpu, 0.0) + val
                    elif name == "system.memory.usage" and a.get("state") == "used":
                        mem[key] = val / MIB
                    elif name == "system.filesystem.usage" and a.get("state") == "used":
                        fs.setdefault(key, {})
                        dev = str(a.get("device", a.get("mountpoint", "")))
                        fs[key][dev] = max(fs[key].get(dev, 0.0), val)
                    elif name == "system.network.io":
                        skey = (env, str(a.get("device", "")), str(a.get("direction", "")))
                        if temporality == 1:        # đã là delta
                            delta = val
                        else:                        # tích lũy: lấy chênh lệch so với lần trước
                            prev = state.get(skey)
                            if prev is None:
                                delta = 0.0
                            elif val >= prev:
                                delta = val - prev
                            else:                    # bộ đếm bị đặt lại
                                delta = val
                            state[skey] = val
                        net[key] = net.get(key, 0.0) + delta / MIB
                    elif name == POWER_METRIC:
                        power.setdefault(key, []).append(val)

    out: Dict[str, List[dict]] = {}
    keys = set(cpu_nonidle) | set(cpu_idle) | set(mem)
    for key in sorted(keys, key=lambda k: (k[0], k[1])):
        env, t = key
        if key in cpu_nonidle:
            vals = list(cpu_nonidle[key].values())
            cpu = sum(vals) / len(vals) * 100.0
        elif key in cpu_idle:
            vals = list(cpu_idle[key].values())
            cpu = (1.0 - sum(vals) / len(vals)) * 100.0
        else:
            cpu = None
        if cpu is None or key not in mem:
            rejected.append("%s %s: thiếu CPU hoặc RAM" % (env, t.isoformat()))
            continue
        w = None
        if key in power:
            w = sum(power[key]) / len(power[key])
            if w <= 0:
                w = None
        out.setdefault(env, []).append({
            "thoiDiem": t.isoformat(),
            "cpuPhanTram": round(max(0.0, min(100.0, cpu)), 2),
            "ramMB": round(mem[key], 2),
            "odiaGB": round(sum(fs.get(key, {}).values()) / GIB, 2),
            "bangThongMB": round(net.get(key, 0.0), 2),
            "congSuatW": round(w, 2) if w is not None else None,
        })
    return out, rejected

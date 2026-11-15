"""Phương án dự phòng khi chưa cài được Collector: đọc số liệu THẬT của máy này bằng psutil, gửi /api/v1/ingest/infra.
  set GREENDASH_API_KEY=...   (PowerShell: $env:GREENDASH_API_KEY="...")
  python tools/psutil_agent.py --moi-truong MT001
"""
import argparse, os, time
from datetime import datetime, timezone

import httpx
import psutil

MIB = 1024 * 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--moi-truong", required=True)
    ap.add_argument("--url", default=os.environ.get("GREENDASH_URL", "http://localhost:8000"))
    ap.add_argument("--chu-ky", type=int, default=60)
    a = ap.parse_args()
    khoa = os.environ.get("GREENDASH_API_KEY", "")
    if not khoa:
        raise SystemExit("Thiếu biến môi trường GREENDASH_API_KEY")
    psutil.cpu_percent(interval=None)
    nc = psutil.net_io_counters()
    prev = nc.bytes_sent + nc.bytes_recv
    while True:
        time.sleep(a.chu_ky)
        nc = psutil.net_io_counters()
        cur = nc.bytes_sent + nc.bytes_recv
        delta = max(cur - prev, 0) / MIB
        prev = cur
        diem = {
            "thoiDiem": datetime.now(timezone.utc).isoformat(),
            "cpuPhanTram": psutil.cpu_percent(interval=None),
            "ramMB": psutil.virtual_memory().used / MIB,
            "odiaGB": psutil.disk_usage(os.path.abspath(os.sep)).used / 1024 ** 3,
            "bangThongMB": delta,
            "congSuatW": None,
        }
        try:
            r = httpx.post(a.url + "/api/v1/ingest/infra", headers={"X-API-Key": khoa},
                           json={"maMoiTruong": a.moi_truong, "diem": [diem]}, timeout=15)
            print(datetime.now().strftime("%H:%M:%S"), r.status_code, r.text[:120])
        except httpx.HTTPError as e:
            print("Lỗi gửi:", e)


if __name__ == "__main__":
    main()

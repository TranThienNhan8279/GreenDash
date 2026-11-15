"""TC04: tăng tải dần. Chạy trên CSDL THỬ NGHIỆM, không chạy trên dữ liệu thật vì ingest ghi dòng mới.
  set GD_API_KEY=... ; set GD_MT=MT_TEST ; set GD_USER=admin ; set GD_PASS=... ; set GD_SP=SP001
  locust -f tests/locustfile.py --host http://localhost:8000
Ngưỡng đạt: p95 < 3 giây, lỗi < 1%.
"""
import os, random
from datetime import datetime, timedelta, timezone

from locust import HttpUser, LoadTestShape, between, task


class NguoiDung(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        r = self.client.post("/api/v1/auth/login", json={"tenDangNhap": os.environ["GD_USER"], "matKhau": os.environ["GD_PASS"]})
        self.h = {"Authorization": "Bearer " + r.json()["token"]}

    @task(3)
    def ingest(self):
        t = datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 400000))   # thời điểm quá khứ ngẫu nhiên, tránh trùng
        d = {"thoiDiem": t.isoformat(), "cpuPhanTram": random.uniform(5, 90), "ramMB": 4000, "odiaGB": 100, "bangThongMB": 5}
        self.client.post("/api/v1/ingest/infra", headers={"X-API-Key": os.environ["GD_API_KEY"]},
                         json={"maMoiTruong": os.environ["GD_MT"], "diem": [d]}, name="/ingest/infra")

    @task(2)
    def dashboard(self):
        self.client.get("/api/v1/dashboard", params={"maSanPham": os.environ["GD_SP"]}, headers=self.h, name="/dashboard")


class TangDan(LoadTestShape):
    """10 người dùng mỗi 30 giây, tối đa 100, chạy 6 phút."""
    def tick(self):
        t = self.get_run_time()
        if t > 360:
            return None
        return (min(10 + int(t // 30) * 10, 100), 10)

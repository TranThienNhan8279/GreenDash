# GreenDash (ENV-10): Bảng điều khiển bền vững cho sản phẩm phần mềm

Đồ án môn **Phương pháp phát triển phần mềm hướng đối tượng**, Khoa Công nghệ Thông tin, Trường Đại học Tài nguyên và Môi trường TP.HCM.

- Giảng viên hướng dẫn: ThS. Phạm Trọng Huynh
- Sinh viên thực hiện: Trần Thiện Nhân, MSSV 1250080123, lớp 12_ĐH_CNPM2

GreenDash thu thập số liệu hạ tầng (CPU, RAM, ổ đĩa, băng thông) qua **OpenTelemetry Collector** và đo kích thước, thời gian tải trang web bằng **Playwright**. Từ đó hệ thống quy đổi ra điện năng và lượng carbon, rồi hiển thị trên dashboard kèm cảnh báo vượt ngưỡng và đề xuất hành động giảm tác động.

Nguyên tắc chính: **mọi con số carbon đều mang nhãn "Đo" hoặc "Ước lượng"**, kèm độ tin cậy và nguồn hệ số phát thải. Khi thiếu hệ số phát thải, hệ thống không công bố số carbon.

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend, API | Python 3.13, FastAPI, Uvicorn, APScheduler, pyodbc, bcrypt |
| Cơ sở dữ liệu | SQL Server Express (`localhost\SQLEXPRESS`, CSDL `GreenDashDB`) |
| Thu thập số liệu hạ tầng | OpenTelemetry Collector Contrib (receiver `hostmetrics`, exporter `otlphttp`) |
| Đo trang web | Playwright (Chromium) |
| Giao diện | HTML, CSS, JavaScript, Chart.js (`backend/static/index.html`) |
| Kiểm thử | pytest, kịch bản SQL kiểm thử trigger/view/stored procedure, Locust |

## Cấu trúc thư mục

```
Greendash/
├── backend/                  FastAPI: main.py (API), auth.py, core.py, rules.py, ingest.py, otlp_mapper.py, jobs.py, db.py
│   └── static/index.html     giao diện dashboard
├── collector/page_collector.py   đo trang web bằng Playwright
├── otel/otelcol-config.yaml      cấu hình OpenTelemetry Collector
├── sql/
│   ├── 01_greendash.sql          bảng, ràng buộc, view, thủ tục quy đổi carbon
│   ├── 02_sua_do_chinh_xac.sql   sửa độ chính xác phép tính (ép FLOAT)
│   ├── 03_trigger_view_store.sql 7 trigger, view, 2 stored procedure, bảng nhật ký
│   └── 04_demo_kiem_thu.sql      11 ca kiểm thử (PASS/FAIL), tự ROLLBACK
├── tools/                    khoi_tao.py (khởi tạo dữ liệu, khóa API), psutil_agent.py, dat_lai_mat_khau.py
├── tests/                    pytest, locustfile
├── docs/
│   ├── diagrams/             file .drawio gốc (mở bằng https://app.diagrams.net)
│   │   ├── 01_UseCase  02_HoatDong  03_TuanTu  04_Lop  05_PhanTich_BCE
│   │   └── 06_TrangThai  07_KienTruc_TrienKhai  08_CSDL
│   ├── images/               ảnh PNG xuất từ các sơ đồ trên + 09_GiaoDien (ảnh chụp màn hình)
│   └── GreenDash_MoTa_Lop_va_CSDL.md
├── HuongDan_SQL_Trigger_View_Store.md
├── requirements.txt
└── .env.example              mẫu cấu hình (bản thật .env KHÔNG đưa lên GitHub)
```

## Cài đặt và chạy (Windows)

**Yêu cầu:** Python 3.11 trở lên, SQL Server Express, ODBC Driver 18 for SQL Server, SSMS.

1. **Tạo CSDL:** mở SSMS, chạy lần lượt `sql/01_greendash.sql`, `sql/02_sua_do_chinh_xac.sql`, `sql/03_trigger_view_store.sql`. Muốn kiểm tra trigger/view/stored procedure thì chạy `sql/04_demo_kiem_thu.sql` (kết quả mong đợi: 11 PASS).
2. **Môi trường Python:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Cấu hình:** chép `.env.example` thành `.env`, sửa chuỗi kết nối cho đúng máy:
   ```
   GREENDASH_DB=DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=GreenDashDB;Trusted_Connection=yes;TrustServerCertificate=yes;
   ```
4. **Khởi tạo dữ liệu, tài khoản admin, khóa API:**
   ```powershell
   python tools\khoi_tao.py --san-pham SP001 --ten "Website demo" --moi-truong MT001 --ten-moi-truong "May ca nhan" --vung VN --admin admin --he-so <kgCO2e/kWh> --nguon "<tên nguồn, năm>" --hieu-luc-tu 2026-01-01
   ```
   Khóa API chỉ in ra **một lần**. Không dán khóa vào mã nguồn hay đưa lên GitHub.
5. **Chạy backend:** `uvicorn backend.main:app --reload`, rồi mở http://localhost:8000.
6. **Chạy Collector** (thư mục chứa `otelcol-contrib.exe`):
   ```powershell
   $env:GREENDASH_API_KEY="<khóa API>"
   .\otelcol-contrib.exe --config otelcol-config.yaml
   ```
7. **Đo trang web** (chỉ đo website của chính mình):
   ```powershell
   $env:GREENDASH_API_KEY="<khóa API>"
   python collector\page_collector.py --lap-phut 30 --loc localhost
   ```
   Danh sách URL được thêm hoặc xóa ngay trên giao diện web (tab "Trang web").
8. **Kiểm thử:** `pytest -q`

## Công thức quy đổi

- Công suất ước lượng: `P (W) = CongSuatNen + k × %CPU` (mặc định 30 W và 0,7 W/% chỉ là điểm khởi đầu, cần hiệu chỉnh bằng thiết bị đo).
- Điện năng: `kWh = P × số giây / 3600 / 1000`.
- Carbon: `gCO2e = kWh × hệ số (kgCO2e/kWh) × 1000`.
- Thứ tự chọn hệ số: hệ số của vùng còn hiệu lực, nếu không có thì hệ số mặc định quốc gia, nếu vẫn không có thì **bỏ qua, không công bố carbon**.

## Bảo mật

- Mật khẩu băm bằng bcrypt, sai 5 lần thì khóa 15 phút.
- Khóa API chỉ lưu dạng băm SHA-256, gửi qua header `X-API-Key`.
- `.env`, khóa API, mật khẩu **không** có trong repository.

"""GreenDash API. Chạy: uvicorn main:app --port 8000   (trong thư mục backend)"""
import csv
import gzip
import io
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import auth
import db
import ingest
import jobs
import rules
from otlp_mapper import map_otlp

log = logging.getLogger("greendash")
logging.basicConfig(level=logging.INFO)
_net_state: dict = {}          # mốc băng thông tích lũy giữa các lần gọi (một tiến trình)
_sched = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _sched.add_job(jobs.chay_gio, "cron", minute=5, id="gio", max_instances=1, coalesce=True)
    _sched.add_job(jobs.chay_ngay, "cron", hour=1, minute=0, id="ngay", max_instances=1, coalesce=True)
    _sched.start()
    yield
    _sched.shutdown(wait=False)


app = FastAPI(title="GreenDash", lifespan=lifespan)
STATIC = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def trang_chu():
    return FileResponse(os.path.join(STATIC, "index.html"))


@app.get("/health")
def health():
    try:
        db.query("SELECT 1 AS x")
        return {"db": "ok"}
    except Exception as e:                                   # noqa
        log.exception("Loi ket noi CSDL")
        raise HTTPException(503, "Không kết nối được CSDL")


# ---------------------------------------------------------------- đăng nhập
class LoginIn(BaseModel):
    tenDangNhap: str = Field(min_length=1, max_length=50)
    matKhau: str = Field(min_length=1, max_length=200)


@app.post("/api/v1/auth/login")
def login(b: LoginIn):
    return {"token": auth.dang_nhap(b.tenDangNhap, b.matKhau)}


@app.get("/api/v1/me/san-pham")
def san_pham_cua_toi(tk: int = Depends(auth.can_dang_nhap)):
    return auth.san_pham_cua_tai_khoan(tk)


# ---------------------------------------------------------------- nhận OTLP từ Collector
def _xu_ly_otlp(ma_sp: str, payload: dict) -> dict:
    diem_theo_mt, tu_choi = map_otlp(payload, _net_state)
    for ma_mt in diem_theo_mt:                                # kiểm tra hết trước khi lưu
        if not ingest.moi_truong_thuoc_san_pham(ma_mt, ma_sp):
            raise HTTPException(401, "Môi trường không thuộc sản phẩm của khóa API")
    tong = 0
    for ma_mt, ds in diem_theo_mt.items():
        n, loi = ingest.luu_diem(ma_mt, ds)
        tong += n
        tu_choi += loi
    if tu_choi:
        log.warning("OTLP tu choi %d diem: %s", len(tu_choi), tu_choi[:5])
    log.info("OTLP: luu %d diem moi", tong)
    return {}


@app.post("/v1/metrics")
async def nhan_otlp(request: Request, x_api_key: str = Header(default="")):
    ma_sp = await run_in_threadpool(ingest.tim_san_pham_theo_khoa, x_api_key)
    if ma_sp is None:
        raise HTTPException(401, "Khóa API không hợp lệ")
    body = await request.body()
    if request.headers.get("content-encoding", "").lower() == "gzip":
        body = gzip.decompress(body)
    if "json" in request.headers.get("content-type", ""):
        payload = json.loads(body)
    else:
        try:
            from google.protobuf.json_format import MessageToDict
            from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
        except ImportError:
            raise HTTPException(415, "Cần cài opentelemetry-proto để nhận protobuf, hoặc dùng encoding: json")
        msg = ExportMetricsServiceRequest()
        msg.ParseFromString(body)
        payload = MessageToDict(msg)
    return await run_in_threadpool(_xu_ly_otlp, ma_sp, payload)


# ---------------------------------------------------------------- nhận trực tiếp (dự phòng, psutil_agent)
class DiemIn(BaseModel):
    thoiDiem: str
    cpuPhanTram: float
    ramMB: float
    odiaGB: float
    bangThongMB: float
    congSuatW: float | None = None


class InfraIn(BaseModel):
    maMoiTruong: str
    diem: list[DiemIn] = Field(min_length=1, max_length=1000)


@app.post("/api/v1/ingest/infra")
def ingest_infra(b: InfraIn, x_api_key: str = Header(default="")):
    ma_sp = ingest.tim_san_pham_theo_khoa(x_api_key)
    if ma_sp is None:
        raise HTTPException(401, "Khóa API không hợp lệ")
    if not ingest.moi_truong_thuoc_san_pham(b.maMoiTruong, ma_sp):
        raise HTTPException(401, "Môi trường không thuộc sản phẩm của khóa API")
    n, tu_choi = ingest.luu_diem(b.maMoiTruong, [d.model_dump() for d in b.diem])
    if n == 0 and tu_choi:
        raise HTTPException(422, {"tuChoi": tu_choi})
    return {"daLuu": n, "tuChoi": tu_choi}


# ---------------------------------------------------------------- số liệu trang
class PageIn(BaseModel):
    url: str = Field(max_length=400, pattern=r"^https?://")
    thoiDiem: str | None = None
    tongKB: float = Field(ge=0)
    soRequest: int = Field(ge=0)
    anhKB: float = Field(ge=0)
    jsKB: float = Field(ge=0)
    cssKB: float = Field(ge=0)
    ttfbMs: float = Field(ge=0)
    taiMs: float = Field(ge=0)
    tyLeLoi: float = Field(ge=0, le=100)


@app.get("/api/v1/ingest/page/urls")
def url_can_do(x_api_key: str = Header(default="")):
    ma_sp = ingest.tim_san_pham_theo_khoa(x_api_key)
    if ma_sp is None:
        raise HTTPException(401, "Khóa API không hợp lệ")
    return {"urls": ingest.trang_da_dang_ky(ma_sp)}


@app.post("/api/v1/ingest/page")
def ingest_page(b: PageIn, x_api_key: str = Header(default="")):
    ma_sp = ingest.tim_san_pham_theo_khoa(x_api_key)
    if ma_sp is None:
        raise HTTPException(401, "Khóa API không hợp lệ")
    try:
        ingest.luu_trang(ma_sp, b.model_dump())
    except PermissionError as e:
        raise HTTPException(403, str(e))
    return {"daLuu": 1}


# ---------------------------------------------------------------- quản lý URL trang web ngay trên giao diện
class TrangIn(BaseModel):
    maSanPham: str = Field(min_length=1, max_length=20)
    url: str = Field(min_length=8, max_length=400)
    laTrangCuaToi: bool = False          # người dùng xác nhận trang thuộc quyền của mình


@app.get("/api/v1/pages")
def ds_trang(maSanPham: str, tk: int = Depends(auth.can_dang_nhap)):
    auth.kiem_tra_quyen_san_pham(tk, maSanPham)
    return db.query("""SELECT t.MaTrang, t.Url, COUNT(v.MaSoLieuTrang) AS SoLanDo, MAX(v.ThoiDiem) AS LanDoCuoi
                       FROM dbo.Trang t LEFT JOIN dbo.SoLieuTrang v ON v.MaTrang = t.MaTrang
                       WHERE t.MaSanPham = ? GROUP BY t.MaTrang, t.Url ORDER BY t.MaTrang""", (maSanPham,))


@app.post("/api/v1/pages")
def them_trang(b: TrangIn, tk: int = Depends(auth.can_dang_nhap)):
    from urllib.parse import urlparse
    auth.kiem_tra_quyen_san_pham(tk, b.maSanPham)
    if not b.laTrangCuaToi:
        raise HTTPException(400, "Hãy xác nhận đây là trang web của bạn hoặc bạn được phép đo")
    url = b.url.strip()
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.netloc or " " in url:
        raise HTTPException(400, "URL không hợp lệ, phải bắt đầu bằng http:// hoặc https://")
    if db.query("SELECT 1 AS x FROM dbo.Trang WHERE MaSanPham = ? AND Url = ?", (b.maSanPham, url)):
        raise HTTPException(409, "URL này đã có trong danh sách")
    db.execute("INSERT INTO dbo.Trang (MaSanPham, Url) VALUES (?, ?)", (b.maSanPham, url))
    return {"daThem": url}


@app.delete("/api/v1/pages/{ma_trang}")
def xoa_trang(ma_trang: int, maSanPham: str, xoaCaSoLieu: bool = False, tk: int = Depends(auth.can_dang_nhap)):
    auth.kiem_tra_quyen_san_pham(tk, maSanPham)
    if not db.query("SELECT 1 AS x FROM dbo.Trang WHERE MaTrang = ? AND MaSanPham = ?", (ma_trang, maSanPham)):
        raise HTTPException(404, "Không tìm thấy trang")
    n = db.query("SELECT COUNT(*) AS n FROM dbo.SoLieuTrang WHERE MaTrang = ?", (ma_trang,))[0]["n"]
    if n and not xoaCaSoLieu:
        raise HTTPException(409, "Trang này đã có %d lần đo. Xóa sẽ mất cả số liệu đo." % n)
    db.execute("DELETE FROM dbo.SoLieuTrang WHERE MaTrang = ?", (ma_trang,))
    db.execute("DELETE FROM dbo.Trang WHERE MaTrang = ? AND MaSanPham = ?", (ma_trang, maSanPham))
    return {"daXoa": ma_trang}


# ---------------------------------------------------------------- dashboard, cảnh báo, báo cáo
@app.get("/api/v1/dashboard")
def dashboard(maSanPham: str, soNgay: int = 14, tk: int = Depends(auth.can_dang_nhap)):
    auth.kiem_tra_quyen_san_pham(tk, maSanPham)
    soNgay = max(1, min(soNgay, 90))
    tu = (datetime.utcnow() - timedelta(days=soNgay)).date()
    return {
        "maSanPham": maSanPham,
        "carbonNgay": db.query("""SELECT Ngay, NangLuongKWh, CarbonG, SoDiem, NhanTongHop, DoTinCayThapNhat, NguonHeSo, SoNguonHeSo
                                  FROM dbo.vw_TongHopCarbonNgay WHERE MaSanPham = ? AND Ngay >= ? ORDER BY Ngay""", (maSanPham, tu)),
        "hieuNangTrang": db.query("SELECT * FROM dbo.vw_HieuNangTrang WHERE MaSanPham = ? ORDER BY TongKBTrungBinh DESC", (maSanPham,)),
        "soLieuGanDay": db.query("""SELECT TOP 180 s.MaMoiTruong, s.ThoiDiem, s.CpuPhanTram, s.RamMB, s.OdiaGB, s.BangThongMB, s.CongSuatW
                                    FROM dbo.SoLieuHaTang s JOIN dbo.MoiTruong m ON m.MaMoiTruong = s.MaMoiTruong
                                    WHERE m.MaSanPham = ? ORDER BY s.ThoiDiem DESC""", (maSanPham,)),
        "soDiemChuaQuyDoi": db.query("""SELECT COUNT(*) AS n FROM dbo.SoLieuHaTang s JOIN dbo.MoiTruong m ON m.MaMoiTruong = s.MaMoiTruong
                                        WHERE m.MaSanPham = ? AND s.TrangThai = N'DaChuanHoa'""", (maSanPham,))[0]["n"],
        "canhBaoMo": db.query("SELECT COUNT(*) AS n FROM dbo.vw_CanhBaoDangMo WHERE MaSanPham = ?", (maSanPham,))[0]["n"],
    }


@app.get("/api/v1/alerts")
def canh_bao(maSanPham: str, tk: int = Depends(auth.can_dang_nhap)):
    auth.kiem_tra_quyen_san_pham(tk, maSanPham)
    return db.query("SELECT * FROM dbo.vw_CanhBaoDangMo WHERE MaSanPham = ? ORDER BY ThoiDiemMo DESC", (maSanPham,))


def _quyen_canh_bao(ma_cb: int, tk: int) -> None:
    r = db.query("""SELECT n.MaSanPham FROM dbo.CanhBao c JOIN dbo.NguongCanhBao n ON n.MaNguong = c.MaNguong
                    WHERE c.MaCanhBao = ?""", (ma_cb,))
    if not r:
        raise HTTPException(404, "Không tìm thấy cảnh báo")
    auth.kiem_tra_quyen_san_pham(tk, r[0]["MaSanPham"])


@app.post("/api/v1/alerts/{ma_cb}/ack")
def ack(ma_cb: int, tk: int = Depends(auth.can_dang_nhap)):
    _quyen_canh_bao(ma_cb, tk)
    if db.execute("UPDATE dbo.CanhBao SET TrangThai = N'DaXacNhan' WHERE MaCanhBao = ? AND TrangThai = N'Mo'", (ma_cb,)) == 0:
        raise HTTPException(409, "Cảnh báo không ở trạng thái Mở")
    return {"ok": True}


class CloseIn(BaseModel):
    ghiChu: str = Field(min_length=3, max_length=300)


@app.post("/api/v1/alerts/{ma_cb}/close")
def close(ma_cb: int, b: CloseIn, tk: int = Depends(auth.can_dang_nhap)):
    _quyen_canh_bao(ma_cb, tk)
    if db.execute("UPDATE dbo.CanhBao SET TrangThai = N'DaDong', GhiChuDong = ? WHERE MaCanhBao = ? AND TrangThai <> N'DaDong'",
                  (b.ghiChu, ma_cb)) == 0:
        raise HTTPException(409, "Cảnh báo đã đóng")
    return {"ok": True}


# ---------------------------------------------------------------- hành động
@app.get("/api/v1/actions")
def ds_hanh_dong(maSanPham: str, tk: int = Depends(auth.can_dang_nhap)):
    auth.kiem_tra_quyen_san_pham(tk, maSanPham)
    return db.query("SELECT * FROM dbo.HanhDong WHERE MaSanPham = ? ORDER BY NgayTao DESC", (maSanPham,))


def _quyen_hanh_dong(ma_hd: int, tk: int) -> None:
    r = db.query("SELECT MaSanPham FROM dbo.HanhDong WHERE MaHanhDong = ?", (ma_hd,))
    if not r:
        raise HTTPException(404, "Không tìm thấy hành động")
    auth.kiem_tra_quyen_san_pham(tk, r[0]["MaSanPham"])


def _doi_trang_thai(ma_hd: int, tk: int, tu: str, den: str, ngay_ap_dung=None):
    _quyen_hanh_dong(ma_hd, tk)
    n = db.execute("UPDATE dbo.HanhDong SET TrangThai = ?, NgayApDung = COALESCE(?, NgayApDung) WHERE MaHanhDong = ? AND TrangThai = ?",
                   (den, ngay_ap_dung, ma_hd, tu))
    if n == 0:
        raise HTTPException(409, "Hành động không ở trạng thái %s" % tu)
    return {"ok": True}


@app.post("/api/v1/actions/{ma_hd}/chap-nhan")
def chap_nhan(ma_hd: int, tk: int = Depends(auth.can_dang_nhap)):
    return _doi_trang_thai(ma_hd, tk, "DeXuat", "DaChapNhan")


@app.post("/api/v1/actions/{ma_hd}/tu-choi")
def tu_choi(ma_hd: int, tk: int = Depends(auth.can_dang_nhap)):
    return _doi_trang_thai(ma_hd, tk, "DeXuat", "TuChoi")


@app.post("/api/v1/actions/{ma_hd}/da-ap-dung")
def da_ap_dung(ma_hd: int, tk: int = Depends(auth.can_dang_nhap)):
    return _doi_trang_thai(ma_hd, tk, "DaChapNhan", "DaApDung", datetime.utcnow().date())


@app.get("/api/v1/actions/{ma_hd}/danh-gia")
def danh_gia(ma_hd: int, soNgay: int = 7, tk: int = Depends(auth.can_dang_nhap)):
    _quyen_hanh_dong(ma_hd, tk)
    try:
        return rules.danh_gia(ma_hd, max(1, min(soNgay, 60)))
    except ValueError as e:
        raise HTTPException(409, str(e))


# ---------------------------------------------------------------- báo cáo CSV, chạy xử lý thủ công
@app.get("/api/v1/reports")
def bao_cao(maSanPham: str, soNgay: int = 30, tk: int = Depends(auth.can_dang_nhap)):
    auth.kiem_tra_quyen_san_pham(tk, maSanPham)
    tu = (datetime.utcnow() - timedelta(days=max(1, min(soNgay, 365)))).date()
    rows = db.query("""SELECT Ngay, NangLuongKWh, CarbonG, SoDiem, NhanTongHop, DoTinCayThapNhat, NguonHeSo
                       FROM dbo.vw_TongHopCarbonNgay WHERE MaSanPham = ? AND Ngay >= ? ORDER BY Ngay""", (maSanPham, tu))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Ngay", "NangLuongKWh", "CarbonG", "SoDiem", "Nhan", "DoTinCayThapNhat", "NguonHeSo"])
    for r in rows:
        w.writerow([r["Ngay"], r["NangLuongKWh"], r["CarbonG"], r["SoDiem"], r["NhanTongHop"], r["DoTinCayThapNhat"], r["NguonHeSo"]])
    return Response("\ufeff" + out.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=greendash_%s.csv" % maSanPham})


@app.post("/api/v1/admin/chay-xu-ly")
def chay_xu_ly(tk: int = Depends(auth.can_dang_nhap)):
    """Chạy ngay quy đổi carbon, cảnh báo, luật đề xuất (tiện khi demo)."""
    return {**jobs.chay_gio(), **jobs.chay_ngay()}

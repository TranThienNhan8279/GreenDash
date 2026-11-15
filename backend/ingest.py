"""Tiếp nhận số liệu: xác thực khóa API, kiểm tra BR09, loại trùng BR19, lưu ở trạng thái DaChuanHoa."""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import db


def tim_san_pham_theo_khoa(khoa: str) -> Optional[str]:
    if not khoa:
        return None
    bam = hashlib.sha256(khoa.encode()).hexdigest()
    rows = db.query("SELECT MaSanPham FROM dbo.SanPham WHERE KhoaApiBam = ? AND TrangThai = N'DangTheoDoi'", (bam,))
    return rows[0]["MaSanPham"] if rows else None


def moi_truong_thuoc_san_pham(ma_mt: str, ma_sp: str) -> bool:
    return bool(db.query("SELECT 1 AS x FROM dbo.MoiTruong WHERE MaMoiTruong = ? AND MaSanPham = ?", (ma_mt, ma_sp)))


def _parse_thoi_diem(s) -> datetime:
    t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if t.tzinfo is not None:
        t = t.astimezone(timezone.utc).replace(tzinfo=None)
    return t.replace(second=0, microsecond=0)


def kiem_tra_diem(d: dict, bay_gio: Optional[datetime] = None) -> Tuple[Optional[dict], Optional[str]]:
    """Trả (điểm đã chuẩn hóa, None) hoặc (None, lý do từ chối)."""
    bay_gio = bay_gio or datetime.utcnow()
    try:
        t = _parse_thoi_diem(d["thoiDiem"])
        cpu = float(d["cpuPhanTram"]); ram = float(d["ramMB"])
        odia = float(d["odiaGB"]); bt = float(d["bangThongMB"])
    except (KeyError, ValueError, TypeError):
        return None, "Thiếu hoặc sai định dạng trường bắt buộc"
    if t > bay_gio + timedelta(minutes=2):
        return None, "Thời điểm ở tương lai"
    if not 0 <= cpu <= 100:
        return None, "CPU ngoài khoảng 0-100"
    if ram < 0 or odia < 0 or bt < 0:
        return None, "RAM, ổ đĩa hoặc băng thông âm"
    w = d.get("congSuatW")
    w = float(w) if w is not None else None
    if w is not None and w <= 0:
        w = None                                   # công suất 0 hoặc âm = không có công suất thật
    return {"thoiDiem": t, "cpu": cpu, "ram": ram, "odia": odia, "bt": bt, "w": w}, None


def luu_diem(ma_mt: str, diem: List[dict]) -> Tuple[int, List[str]]:
    """Lưu các điểm của một môi trường trong MỘT transaction. Trả (số dòng mới, danh sách từ chối)."""
    hop_le, tu_choi = [], []
    for d in diem:
        p, loi = kiem_tra_diem(d)
        if loi:
            tu_choi.append("%s %s: %s" % (ma_mt, d.get("thoiDiem"), loi))
        else:
            hop_le.append(p)
    if not hop_le:
        return 0, tu_choi
    sql = """INSERT INTO dbo.SoLieuHaTang (MaMoiTruong, ThoiDiem, CpuPhanTram, RamMB, OdiaGB, BangThongMB, CongSuatW)
             SELECT ?, CAST(? AS DATETIME2(0)), CAST(? AS DECIMAL(5,2)), CAST(? AS DECIMAL(12,2)),
                    CAST(? AS DECIMAL(12,2)), CAST(? AS DECIMAL(14,2)), CAST(? AS DECIMAL(10,2))
             WHERE NOT EXISTS (SELECT 1 FROM dbo.SoLieuHaTang WHERE MaMoiTruong = ? AND ThoiDiem = CAST(? AS DATETIME2(0)))"""
    moi = 0
    with db.connect() as cn:
        cur = cn.cursor()
        try:
            for p in hop_le:
                cur.execute(sql, (ma_mt, p["thoiDiem"], p["cpu"], p["ram"], p["odia"], p["bt"], p["w"], ma_mt, p["thoiDiem"]))
                moi += max(cur.rowcount, 0)
            cn.commit()
        except Exception:
            cn.rollback()
            raise
    return moi, tu_choi


def trang_da_dang_ky(ma_sp: str) -> list:
    return [r["Url"] for r in db.query("SELECT Url FROM dbo.Trang WHERE MaSanPham = ?", (ma_sp,))]


def luu_trang(ma_sp: str, p: dict) -> None:
    rows = db.query("SELECT MaTrang FROM dbo.Trang WHERE MaSanPham = ? AND Url = ?", (ma_sp, p["url"]))
    if not rows:
        raise PermissionError("URL chưa được đăng ký cho sản phẩm này")
    t = _parse_thoi_diem(p["thoiDiem"]) if p.get("thoiDiem") else datetime.utcnow().replace(second=0, microsecond=0)
    db.execute("""INSERT INTO dbo.SoLieuTrang (MaTrang, ThoiDiem, TongKB, SoRequest, AnhKB, JsKB, CssKB, TtfbMs, TaiMs, TyLeLoi)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
               (rows[0]["MaTrang"], t, p["tongKB"], p["soRequest"], p["anhKB"], p["jsKB"], p["cssKB"],
                p["ttfbMs"], p["taiMs"], p["tyLeLoi"]))

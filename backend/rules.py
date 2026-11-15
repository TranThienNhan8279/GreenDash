"""Luật đề xuất hành động (chạy mỗi ngày) và đánh giá hiệu quả sau khi áp dụng."""
from datetime import date, datetime, timedelta

import core
import db

NGUONG_CPU_THAP = 20.0      # %CPU trung bình 7 ngày dưới mức này => đề xuất thu nhỏ/gộp máy
SO_NGAY_TOI_THIEU = 3       # cần ít nhất số ngày có dữ liệu này mới kết luận
NGUONG_TRANG_NANG_KB = 2000.0
NGUONG_ANH_PHAN_TRAM = 50.0


def _them_neu_chua_co(ma_sp: str, loai: str, mo_ta: str) -> int:
    return db.execute("""INSERT INTO dbo.HanhDong (MaSanPham, Loai, MoTa)
                         SELECT ?, ?, ?
                         WHERE NOT EXISTS (SELECT 1 FROM dbo.HanhDong WHERE MaSanPham = ? AND Loai = ?
                                           AND TrangThai IN (N'DeXuat', N'DaChapNhan'))""",
                      (ma_sp, loai, mo_ta, ma_sp, loai))


def de_xuat_hanh_dong() -> int:
    tao = 0
    for sp in db.query("SELECT MaSanPham FROM dbo.SanPham WHERE TrangThai = N'DangTheoDoi'"):
        ma = sp["MaSanPham"]
        r = db.query("""SELECT AVG(s.CpuPhanTram) AS Cpu, COUNT(DISTINCT CAST(s.ThoiDiem AS DATE)) AS SoNgay
                        FROM dbo.SoLieuHaTang s JOIN dbo.MoiTruong m ON m.MaMoiTruong = s.MaMoiTruong
                        WHERE m.MaSanPham = ? AND s.ThoiDiem >= DATEADD(DAY, -7, SYSUTCDATETIME())""", (ma,))[0]
        if r["Cpu"] is not None and r["SoNgay"] >= SO_NGAY_TOI_THIEU and float(r["Cpu"]) < NGUONG_CPU_THAP:
            tao += _them_neu_chua_co(ma, "ThuNhoHoacGopMay",
                                     "CPU trung bình 7 ngày chỉ %.1f%%: cân nhắc thu nhỏ cấu hình hoặc gộp máy." % float(r["Cpu"]))
        for t in db.query("SELECT Url, TongKBTrungBinh, AnhKBTrungBinh FROM dbo.vw_HieuNangTrang WHERE MaSanPham = ?", (ma,)):
            tong = float(t["TongKBTrungBinh"] or 0)
            if tong > NGUONG_TRANG_NANG_KB:
                tao += _them_neu_chua_co(ma, "GiamDungLuongTrang",
                                         "Trang %s nặng %.0f KB (ngưỡng %.0f KB): nén ảnh, giảm JS/CSS, bật cache." % (t["Url"], tong, NGUONG_TRANG_NANG_KB))
                if tong > 0 and float(t["AnhKBTrungBinh"] or 0) / tong * 100 > NGUONG_ANH_PHAN_TRAM:
                    tao += _them_neu_chua_co(ma, "NenAnh", "Ảnh chiếm hơn %.0f%% dung lượng trang %s: dùng WebP/AVIF, lazy-load." % (NGUONG_ANH_PHAN_TRAM, t["Url"]))
    return tao


def danh_gia(ma_hanh_dong: int, so_ngay: int = 7) -> dict:
    """So tổng carbon N ngày trước và N ngày sau ngày áp dụng. Ném ValueError nếu chưa đủ điều kiện."""
    h = db.query("SELECT MaSanPham, TrangThai, NgayApDung FROM dbo.HanhDong WHERE MaHanhDong = ?", (ma_hanh_dong,))
    if not h:
        raise LookupError("Không tìm thấy hành động")
    h = h[0]
    if h["TrangThai"] != "DaApDung" or h["NgayApDung"] is None:
        raise ValueError("Hành động chưa ở trạng thái Đã áp dụng")
    ngay = h["NgayApDung"]
    if not core.du_ngay_sau_ap_dung(ngay, datetime.utcnow().date(), so_ngay):
        raise ValueError("Chưa đủ %d ngày sau khi áp dụng" % so_ngay)

    def ky(tu: date, den: date):   # [tu, den)
        rows = db.query("""SELECT Ngay, CarbonG, NhanTongHop FROM dbo.vw_TongHopCarbonNgay
                           WHERE MaSanPham = ? AND Ngay >= ? AND Ngay < ?""", (h["MaSanPham"], tu, den))
        return rows

    truoc = ky(ngay - timedelta(days=so_ngay), ngay)
    sau = ky(ngay, ngay + timedelta(days=so_ngay))
    if len(truoc) < so_ngay or len(sau) < so_ngay:
        raise ValueError("Thiếu dữ liệu: kỳ trước có %d/%d ngày, kỳ sau có %d/%d ngày" % (len(truoc), so_ngay, len(sau), so_ngay))
    t = sum(float(r["CarbonG"]) for r in truoc)
    s = sum(float(r["CarbonG"]) for r in sau)
    giam, pt = core.muc_giam(t, s)
    nhan = core.nhan_danh_gia([r["NhanTongHop"] for r in truoc], [r["NhanTongHop"] for r in sau])
    return {"maHanhDong": ma_hanh_dong, "soNgay": so_ngay, "carbonTruocG": t, "carbonSauG": s,
            "giamG": giam, "giamPhanTram": pt, "nhan": nhan}

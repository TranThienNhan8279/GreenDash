"""Khởi tạo dữ liệu nền: sản phẩm + khóa API, môi trường, tài khoản, trang cần đo, ngưỡng, hệ số phát thải.
Ví dụ:
  python tools/khoi_tao.py --san-pham SP001 --ten "Website cua toi" --moi-truong MT001 \
      --admin admin --url https://example.com/ \
      --he-so <so kg CO2e/kWh THAT> --nguon "<ten nguon, nam, don vi>" --hieu-luc-tu 2024-01-01
Khóa API chỉ in ra MỘT lần; trong CSDL chỉ lưu SHA-256.
"""
import argparse, getpass, hashlib, os, secrets, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import auth, db  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--san-pham", required=True)
    ap.add_argument("--ten", required=True)
    ap.add_argument("--moi-truong", required=True)
    ap.add_argument("--ten-moi-truong", default="Production")
    ap.add_argument("--vung", default="VN", help="MaVung trong VungLuoiDien (để trống = chỉ dùng hệ số mặc định quốc gia)")
    ap.add_argument("--admin", required=True)
    ap.add_argument("--url", action="append", default=[], help="URL thuộc quyền của bạn, lặp được")
    ap.add_argument("--he-so", type=float, help="hệ số phát thải kg CO2e/kWh (số thật, có nguồn)")
    ap.add_argument("--nguon", help="tên nguồn, năm, đơn vị của hệ số")
    ap.add_argument("--hieu-luc-tu", default="2024-01-01")
    ap.add_argument("--tao-lai-khoa", action="store_true")
    a = ap.parse_args()

    khoa = None
    if not db.query("SELECT 1 AS x FROM dbo.SanPham WHERE MaSanPham = ?", (a.san_pham,)) or a.tao_lai_khoa:
        khoa = secrets.token_urlsafe(32)
        bam = hashlib.sha256(khoa.encode()).hexdigest()
        if db.query("SELECT 1 AS x FROM dbo.SanPham WHERE MaSanPham = ?", (a.san_pham,)):
            db.execute("UPDATE dbo.SanPham SET KhoaApiBam = ? WHERE MaSanPham = ?", (bam, a.san_pham))
        else:
            db.execute("INSERT INTO dbo.SanPham (MaSanPham, TenSanPham, KhoaApiBam) VALUES (?, ?, ?)", (a.san_pham, a.ten, bam))

    if not db.query("SELECT 1 AS x FROM dbo.MoiTruong WHERE MaMoiTruong = ?", (a.moi_truong,)):
        db.execute("INSERT INTO dbo.MoiTruong (MaMoiTruong, MaSanPham, TenMoiTruong, MaVung) VALUES (?, ?, ?, ?)",
                   (a.moi_truong, a.san_pham, a.ten_moi_truong, a.vung or None))

    if not db.query("SELECT 1 AS x FROM dbo.TaiKhoan WHERE TenDangNhap = ?", (a.admin,)):
        mk = getpass.getpass("Mật khẩu cho %s (tối thiểu 8 ký tự): " % a.admin)
        if len(mk) < 8:
            sys.exit("Mật khẩu quá ngắn")
        db.execute("INSERT INTO dbo.TaiKhoan (TenDangNhap, MatKhauBam) VALUES (?, ?)", (a.admin, auth.bam_mat_khau(mk)))
    tk = db.query("SELECT MaTaiKhoan FROM dbo.TaiKhoan WHERE TenDangNhap = ?", (a.admin,))[0]["MaTaiKhoan"]
    if not db.query("SELECT 1 AS x FROM dbo.TaiKhoanSanPham WHERE MaTaiKhoan = ? AND MaSanPham = ?", (tk, a.san_pham)):
        db.execute("INSERT INTO dbo.TaiKhoanSanPham (MaTaiKhoan, MaSanPham) VALUES (?, ?)", (tk, a.san_pham))

    for u in a.url:
        if not db.query("SELECT 1 AS x FROM dbo.Trang WHERE MaSanPham = ? AND Url = ?", (a.san_pham, u)):
            db.execute("INSERT INTO dbo.Trang (MaSanPham, Url) VALUES (?, ?)", (a.san_pham, u))

    if not db.query("SELECT 1 AS x FROM dbo.NguongCanhBao WHERE MaSanPham = ? AND ChiTieu = N'Cpu'", (a.san_pham,)):
        db.execute("INSERT INTO dbo.NguongCanhBao (MaSanPham, ChiTieu, ToanTu, GiaTri, MoTa) VALUES (?, N'Cpu', '>', 85, N'CPU trung bình 1 giờ vượt 85%')",
                   (a.san_pham,))

    if a.he_so is not None:
        if not a.nguon:
            sys.exit("Phải ghi --nguon cho hệ số phát thải")
        db.execute("INSERT INTO dbo.HeSoPhatThai (MaVung, LaMacDinhQuocGia, HeSoKgKwh, NguonHeSo, HieuLucTu) VALUES (NULL, 1, ?, ?, ?)",
                   (a.he_so, a.nguon, a.hieu_luc_tu))
        print("Đã thêm hệ số mặc định quốc gia.")
    elif not db.query("SELECT 1 AS x FROM dbo.HeSoPhatThai"):
        print("CHÚ Ý: chưa có hệ số phát thải nào. Hệ thống sẽ BỎ QUA quy đổi carbon cho tới khi bạn nhập (--he-so, --nguon).")

    print("Xong.")
    if khoa:
        print("KHÓA API (lưu lại, sẽ không hiện lần nữa): " + khoa)


if __name__ == "__main__":
    main()

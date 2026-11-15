"""Đặt lại mật khẩu cho một tài khoản (khi quên). Mật khẩu nhập qua bàn phím, không hiện trên màn hình.
Ví dụ:  python tools\\dat_lai_mat_khau.py --admin admin
Đồng thời mở khóa tài khoản nếu đang bị khóa do nhập sai nhiều lần.
"""
import argparse, getpass, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import auth, db  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin", required=True, help="Tên đăng nhập cần đặt lại")
    a = ap.parse_args()
    if not db.query("SELECT 1 AS x FROM dbo.TaiKhoan WHERE TenDangNhap = ?", (a.admin,)):
        sys.exit("Không có tài khoản '%s'. Xem danh sách: SELECT TenDangNhap FROM dbo.TaiKhoan" % a.admin)
    mk = getpass.getpass("Mật khẩu mới (tối thiểu 8 ký tự): ")
    if len(mk) < 8:
        sys.exit("Mật khẩu quá ngắn")
    if getpass.getpass("Nhập lại mật khẩu: ") != mk:
        sys.exit("Hai lần nhập không khớp")
    db.execute("UPDATE dbo.TaiKhoan SET MatKhauBam = ?, SoLanSai = 0, KhoaDen = NULL, HoatDong = 1 WHERE TenDangNhap = ?",
               (auth.bam_mat_khau(mk), a.admin))
    print("Đã đặt lại mật khẩu cho", a.admin)


if __name__ == "__main__":
    main()

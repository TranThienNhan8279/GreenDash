"""Đăng nhập (khóa 15 phút sau 5 lần sai), phiên làm việc trong bộ nhớ, kiểm tra quyền sản phẩm."""
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Header, HTTPException

import core
import db

THONG_BAO_CHUNG = "Thông tin đăng nhập không đúng hoặc tài khoản đang tạm khóa."
_DUMMY = bcrypt.hashpw(b"dummy", bcrypt.gensalt())    # để thời gian phản hồi không lộ tài khoản có tồn tại
_phien: dict = {}                                       # token -> (MaTaiKhoan, hết hạn); đủ cho đồ án, 1 tiến trình
HAN_PHIEN_GIO = 8


def bam_mat_khau(mat_khau: str) -> str:
    return bcrypt.hashpw(mat_khau.encode()[:72], bcrypt.gensalt()).decode()


def dang_nhap(ten: str, mat_khau: str) -> str:
    now = datetime.utcnow()
    rows = db.query("SELECT MaTaiKhoan, MatKhauBam, SoLanSai, KhoaDen, HoatDong FROM dbo.TaiKhoan WHERE TenDangNhap = ?", (ten,))
    if not rows:
        bcrypt.checkpw(b"x", _DUMMY)
        raise HTTPException(401, THONG_BAO_CHUNG)
    t = rows[0]
    dung = bcrypt.checkpw(mat_khau.encode()[:72], t["MatKhauBam"].encode())
    dang_khoa = t["KhoaDen"] is not None and t["KhoaDen"] > now
    if dang_khoa or not t["HoatDong"]:
        raise HTTPException(401, THONG_BAO_CHUNG)            # khóa thì đúng mật khẩu cũng không vào được
    if not dung:
        if core.bi_khoa_sau_lan_sai(t["SoLanSai"]):
            db.execute("UPDATE dbo.TaiKhoan SET SoLanSai = 0, KhoaDen = ? WHERE MaTaiKhoan = ?",
                       (now + timedelta(minutes=core.PHUT_KHOA), t["MaTaiKhoan"]))
        else:
            db.execute("UPDATE dbo.TaiKhoan SET SoLanSai = SoLanSai + 1 WHERE MaTaiKhoan = ?", (t["MaTaiKhoan"],))
        raise HTTPException(401, THONG_BAO_CHUNG)
    db.execute("UPDATE dbo.TaiKhoan SET SoLanSai = 0, KhoaDen = NULL WHERE MaTaiKhoan = ?", (t["MaTaiKhoan"],))
    token = secrets.token_urlsafe(32)
    _phien[token] = (t["MaTaiKhoan"], now + timedelta(hours=HAN_PHIEN_GIO))
    return token


def can_dang_nhap(authorization: str = Header(default="")) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Cần đăng nhập")
    p = _phien.get(authorization[7:])
    if not p or p[1] < datetime.utcnow():
        raise HTTPException(401, "Phiên đăng nhập hết hạn")
    return p[0]


def kiem_tra_quyen_san_pham(ma_tai_khoan: int, ma_san_pham: str) -> None:
    ok = db.query("SELECT 1 AS x FROM dbo.TaiKhoanSanPham WHERE MaTaiKhoan = ? AND MaSanPham = ?", (ma_tai_khoan, ma_san_pham))
    if not ok:
        raise HTTPException(403, "Bạn không được gán sản phẩm này")


def san_pham_cua_tai_khoan(ma_tai_khoan: int) -> list:
    return db.query("""SELECT sp.MaSanPham, sp.TenSanPham FROM dbo.TaiKhoanSanPham t
                       JOIN dbo.SanPham sp ON sp.MaSanPham = t.MaSanPham WHERE t.MaTaiKhoan = ?""", (ma_tai_khoan,))

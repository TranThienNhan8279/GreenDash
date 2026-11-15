import os, sys
from datetime import date, datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import core
from ingest import kiem_tra_diem

NOW = datetime(2026, 10, 28, 12, 0, 0)


def test_nang_luong_va_carbon():
    p = core.cong_suat_uoc_luong(30, 0.7, 50)          # 30 + 35 = 65 W
    assert p == 65
    kwh = core.nang_luong_kwh(p, 3600)                 # 65 W trong 1 giờ = 0.065 kWh
    assert abs(kwh - 0.065) < 1e-9
    assert abs(core.carbon_gam(kwh, 0.5) - 32.5) < 1e-9   # 0.065 kWh x 0.5 kg/kWh = 32.5 g


def test_do_tin_cay_va_loai():
    assert core.loai_du_lieu(True) == "Do" and core.loai_du_lieu(False) == "UocLuong"
    assert core.phan_loai_do_tin_cay(True, False) == "Cao"
    assert core.phan_loai_do_tin_cay(False, False) == "TrungBinh"
    assert core.phan_loai_do_tin_cay(False, True) == "Thap"


def test_nhan_tong_hop():
    assert core.nhan_tong_hop(["Do", "Do"]) == "Do"
    assert core.nhan_tong_hop(["UocLuong", "UocLuong"]) == "UocLuong"
    assert core.nhan_tong_hop(["Do", "UocLuong"]) == "UocLuongMotPhan"


def test_vuot_nguong():
    assert core.vuot_nguong(90, ">", 85) and not core.vuot_nguong(80, ">", 85)
    assert core.vuot_nguong(5, "<", 10) and not core.vuot_nguong(None, ">", 1)


def test_du_ngay_va_muc_giam():
    d = date(2026, 10, 1)
    assert not core.du_ngay_sau_ap_dung(d, date(2026, 10, 7), 7)
    assert core.du_ngay_sau_ap_dung(d, date(2026, 10, 8), 7)
    giam, pt = core.muc_giam(200, 150)
    assert giam == 50 and pt == 25
    assert core.muc_giam(0, 0) == (0, None)            # chống chia cho 0
    assert core.nhan_danh_gia(["Do"], ["Do"]) == "Do"
    assert core.nhan_danh_gia(["Do"], ["UocLuongMotPhan"]) == "UocLuong"


def test_khoa_tai_khoan():
    assert not core.bi_khoa_sau_lan_sai(3) and core.bi_khoa_sau_lan_sai(4)   # lần sai thứ 5 thì khóa
    assert core.PHUT_KHOA == 15


def base(**kw):
    d = {"thoiDiem": "2026-10-28T11:59:30Z", "cpuPhanTram": 10, "ramMB": 100, "odiaGB": 5, "bangThongMB": 1}
    d.update(kw); return d


def test_kiem_tra_diem_br09():
    p, loi = kiem_tra_diem(base(), NOW)
    assert loi is None and p["thoiDiem"] == datetime(2026, 10, 28, 11, 59) and p["w"] is None
    assert kiem_tra_diem(base(cpuPhanTram=150), NOW)[1]
    assert kiem_tra_diem(base(ramMB=-1), NOW)[1]
    assert kiem_tra_diem(base(thoiDiem="2026-10-29T00:00:00Z"), NOW)[1]       # tương lai
    assert kiem_tra_diem(base(congSuatW=0), NOW)[0]["w"] is None              # 0 W = không có watt thật
    assert kiem_tra_diem(base(congSuatW=-5), NOW)[0]["w"] is None
    assert kiem_tra_diem(base(congSuatW=70), NOW)[0]["w"] == 70
    assert kiem_tra_diem({"thoiDiem": "x"}, NOW)[1]

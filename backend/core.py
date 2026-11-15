"""Các hàm lõi thuần (không đụng CSDL) để kiểm thử TC05. Công thức khớp usp_QuyDoiCarbon."""
from datetime import date, timedelta
from typing import Iterable, Optional

SO_LAN_SAI_TOI_DA = 5
PHUT_KHOA = 15


def cong_suat_uoc_luong(nen_w: float, k_w_theo_cpu: float, cpu_phan_tram: float) -> float:
    """P(W) = nền + k * %CPU."""
    return nen_w + k_w_theo_cpu * cpu_phan_tram


def nang_luong_kwh(cong_suat_w: float, giay: int) -> float:
    return cong_suat_w * (giay / 3600.0) / 1000.0


def carbon_gam(kwh: float, he_so_kg_kwh: float) -> float:
    return kwh * he_so_kg_kwh * 1000.0


def phan_loai_do_tin_cay(co_cong_suat_that: bool, he_so_mac_dinh_quoc_gia: bool) -> str:
    if co_cong_suat_that:
        return "Cao"
    return "Thap" if he_so_mac_dinh_quoc_gia else "TrungBinh"


def loai_du_lieu(co_cong_suat_that: bool) -> str:
    return "Do" if co_cong_suat_that else "UocLuong"


def nhan_tong_hop(loai: Iterable[str]) -> str:
    """BR12: có một số liệu Ước lượng thì tổng không còn là 'Đo'."""
    ds = list(loai)
    if not ds:
        return "KhongCoDuLieu"
    uoc = sum(1 for x in ds if x == "UocLuong")
    if uoc == 0:
        return "Do"
    if uoc == len(ds):
        return "UocLuong"
    return "UocLuongMotPhan"


def vuot_nguong(gia_tri: Optional[float], toan_tu: str, nguong: float) -> bool:
    if gia_tri is None:
        return False
    return gia_tri > nguong if toan_tu == ">" else gia_tri < nguong


def du_ngay_sau_ap_dung(ngay_ap_dung: date, hom_nay: date, so_ngay: int) -> bool:
    """Đủ N ngày kể từ ngày áp dụng (ngày áp dụng là ngày đầu của kỳ 'sau')."""
    return hom_nay >= ngay_ap_dung + timedelta(days=so_ngay)


def muc_giam(truoc: float, sau: float):
    giam = truoc - sau
    phan_tram = None if truoc == 0 else giam / truoc * 100.0   # chống chia cho 0
    return giam, phan_tram


def nhan_danh_gia(nhan_truoc: Iterable[str], nhan_sau: Iterable[str]) -> str:
    """Có bất kỳ số liệu không phải 'Do' trong hai kỳ thì kết quả là Ước lượng."""
    return "Do" if all(x == "Do" for x in list(nhan_truoc) + list(nhan_sau)) else "UocLuong"


def bi_khoa_sau_lan_sai(so_lan_sai_hien_tai: int) -> bool:
    return so_lan_sai_hien_tai + 1 >= SO_LAN_SAI_TOI_DA

# GreenDash: mô tả lớp và cơ sở dữ liệu

Tài liệu này sinh từ cùng một nguồn dữ liệu với sơ đồ lớp, sơ đồ logic và script SQL nên tên lớp, bảng, cột luôn khớp nhau.

## A. Danh sách lớp (mục 3.1.2)

| STT | Lớp | Trách nhiệm |
|---|---|---|
| 1 | VaiTro | Định nghĩa vai trò người dùng và phạm vi chức năng. |
| 2 | TaiKhoan | Quản lý tài khoản, xác thực mật khẩu, trạng thái khóa và quyền truy cập sản phẩm (BR13, BR14, BR15). |
| 3 | PhienLamViec | Phiên đăng nhập và token của người dùng. |
| 4 | NhatKyHeThong | Ghi nhật ký thao tác quan trọng (đăng nhập, đổi mật khẩu, xuất báo cáo...). |
| 5 | SanPham | Sản phẩm phần mềm cần giám sát; giữ khóa API cho Collector (BR16). |
| 6 | VungLuoiDien | Vùng lưới điện, cơ sở để chọn hệ số phát thải (BR06). |
| 7 | TrungTamDuLieu | Trung tâm dữ liệu cùng vị trí địa lý (kiểu geography) và vùng lưới điện. |
| 8 | HeSoPhatThai | Hệ số phát thải lưới điện (gCO2e/kWh) theo vùng, kèm nguồn và thời hạn hiệu lực (BR18). |
| 9 | MoiTruong | Môi trường triển khai của sản phẩm (dev, staging, prod), gắn trung tâm dữ liệu (BR07, BR17). |
| 10 | Trang | Trang web hoặc màn hình được đo kích thước, hiệu năng. |
| 11 | SoLieuHaTang | Số liệu tài nguyên hạ tầng; có cờ công suất thật để chọn Đo hay Ước lượng (BR02, BR09, BR19). |
| 12 | SoLieuTrang | Số liệu kích thước trang và hiệu năng theo từng lần đo (BR09, BR19). |
| 13 | KetQuaCarbon | Kết quả năng lượng và carbon; luôn mang LoaiDuLieu, DoTinCay, NguonHeSo (BR01-BR08). |
| 14 | NguongCanhBao | Ngưỡng cảnh báo và mục tiêu giảm tác động. |
| 15 | CanhBao | Cảnh báo vượt ngưỡng, có vòng đời Mới, Đã xác nhận, Đã đóng (BR10). |
| 16 | LoaiHanhDong | Danh mục loại hành động giảm tác động (nén ảnh, bật cache, tắt máy chủ nhàn rỗi, chuyển vùng). |
| 17 | HanhDongGiamTacDong | Hành động giảm tác động, từ đề xuất đến áp dụng; mức giảm đề xuất luôn là ước lượng (BR20). |
| 18 | DanhGiaHieuQua | Kết quả so sánh trước và sau khi áp dụng hành động (BR11, BR12). |
| 19 | BaoCao | Báo cáo tổng hợp, luôn kèm tỷ lệ dữ liệu ước lượng và ghi chú phương pháp (BR04). |

## B. Quan hệ giữa các lớp

| Lớp A | Bản số A | Lớp B | Bản số B | Ý nghĩa |
|---|---|---|---|---|
| VaiTro | 1 | TaiKhoan | * | có |
| TaiKhoan | 1 | PhienLamViec | * | mở |
| TaiKhoan | 0..1 | NhatKyHeThong | * | tạo ra |
| TaiKhoan | * | SanPham | * | được truy cập |
| TaiKhoan | 1 | BaoCao | * | lập |
| SanPham | 1 | BaoCao | * | có |
| SanPham | 1 | NguongCanhBao | * | đặt cho |
| TrungTamDuLieu | 0..1 | MoiTruong | * | đặt tại |
| TrungTamDuLieu | * | VungLuoiDien | 1 | thuộc |
| HeSoPhatThai | * | VungLuoiDien | 1 | áp dụng cho |
| SoLieuHaTang | 1 | KetQuaCarbon | 0..1 | sinh ra |
| HeSoPhatThai | 1 | KetQuaCarbon | * | dùng để tính |
| NguongCanhBao | 1 | CanhBao | * | sinh |
| MoiTruong | 0..1 | NguongCanhBao | * | áp dụng |
| MoiTruong | 1 | CanhBao | * | phát sinh |
| LoaiHanhDong | 1 | HanhDongGiamTacDong | * | phân loại |
| MoiTruong | 1 | HanhDongGiamTacDong | * | áp dụng cho |
| HanhDongGiamTacDong | 1 | DanhGiaHieuQua | * | được đánh giá |
| SanPham | 1 | MoiTruong | * | gồm (hợp thành) |
| MoiTruong | 1 | Trang | * | gồm (hợp thành) |
| Trang | 1 | SoLieuTrang | * | gồm (hợp thành) |
| MoiTruong | 1 | SoLieuHaTang | * | gồm (hợp thành) |

## C. Mô tả chi tiết từng lớp (mục 3.1.3)

### VaiTro

**Trách nhiệm:** Định nghĩa vai trò người dùng và phạm vi chức năng.

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaVaiTro | string | PK | Có |
| TenVaiTro | string |  | Có |
| MoTa | string |  | Không |

**Phương thức:** `layVaiTro(maVaiTro)`

### TaiKhoan

**Trách nhiệm:** Quản lý tài khoản, xác thực mật khẩu, trạng thái khóa và quyền truy cập sản phẩm (BR13, BR14, BR15).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaTaiKhoan | string | PK | Có |
| TenDangNhap | string |  | Có |
| MatKhauBam | string |  | Có |
| Salt | string |  | Có |
| HoTen | string |  | Có |
| Email | string |  | Có |
| MaVaiTro | string | FK → VaiTro | Có |
| TrangThai | bool |  | Có |
| SoLanSai | int |  | Có |
| KhoaDen | DateTime |  | Không |

**Phương thức:** `layTatCa()`, `timTheoTenDangNhap(tenDN)`, `tonTaiTenDangNhap(tenDN)`, `soKhopMatKhau(matKhau)`, `kiemTraMatKhauMoi(moi, xacNhan)`, `datMatKhau(moi)`, `dangBiKhoa()`, `tangBoDemSai()`, `datLaiBoDemSai()`, `khoa()`, `moKhoa()`, `coQuyenTruyCap(maSP)`, `luu(dto)`

### PhienLamViec

**Trách nhiệm:** Phiên đăng nhập và token của người dùng.

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaPhien | string | PK | Có |
| MaTaiKhoan | string | FK → TaiKhoan | Có |
| Token | string |  | Có |
| ThoiDiemTao | DateTime |  | Có |
| HanDung | DateTime |  | Có |
| HieuLuc | bool |  | Có |

**Phương thức:** `taoToken(maTK, vaiTro)`, `kiemTraHieuLuc(token)`, `voHieuHoa(token)`, `voHieuHoaCu(maTK)`

### NhatKyHeThong

**Trách nhiệm:** Ghi nhật ký thao tác quan trọng (đăng nhập, đổi mật khẩu, xuất báo cáo...).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaNhatKy | long | PK | Có |
| MaTaiKhoan | string | FK → TaiKhoan | Không |
| HanhDong | string |  | Có |
| ChiTiet | string |  | Không |
| ThoiDiem | DateTime |  | Có |

**Phương thức:** `ghi(maTK, hanhDong)`

### SanPham

**Trách nhiệm:** Sản phẩm phần mềm cần giám sát; giữ khóa API cho Collector (BR16).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaSanPham | string | PK | Có |
| TenSanPham | string |  | Có |
| MoTa | string |  | Không |
| LoaiSanPham | string |  | Có |
| KhoaAPI | string |  | Có |
| TrangThai | string |  | Có |

**Phương thức:** `layTatCa()`, `xacThucKhoaAPI(khoaAPI)`, `tonTaiMa(maSP)`, `luu(dto)`, `ngungTheoDoi()`, `ganQuyenTruyCap(maTK, dsSP)`

### VungLuoiDien

**Trách nhiệm:** Vùng lưới điện, cơ sở để chọn hệ số phát thải (BR06).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaVung | string | PK | Có |
| TenVung | string |  | Có |
| QuocGia | string |  | Có |

**Phương thức:** `layVung(maVung)`

### TrungTamDuLieu

**Trách nhiệm:** Trung tâm dữ liệu cùng vị trí địa lý (kiểu geography) và vùng lưới điện.

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaTrungTam | string | PK | Có |
| TenTrungTam | string |  | Có |
| NhaCungCap | string |  | Có |
| MaVung | string | FK → VungLuoiDien | Có |
| ViDo | decimal |  | Có |
| KinhDo | decimal |  | Có |
| ViTri | geography |  | Có |

**Phương thức:** `layTatCa()`, `layTrungTam(maTrungTam)`, `kiemTraToaDo(viDo, kinhDo)`, `luu(dto)`, `xoa()`

### HeSoPhatThai

**Trách nhiệm:** Hệ số phát thải lưới điện (gCO2e/kWh) theo vùng, kèm nguồn và thời hạn hiệu lực (BR18).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaHeSo | string | PK | Có |
| MaVung | string | FK → VungLuoiDien | Có |
| GiaTri | decimal |  | Có |
| Nam | int |  | Có |
| NguonHeSo | string |  | Có |
| HieuLucTu | DateTime |  | Có |
| HieuLucDen | DateTime |  | Không |
| LaMacDinhQuocGia | bool |  | Có |

**Phương thức:** `layTatCa()`, `layHeSo(vung, thoiDiem)`, `kiemTraHopLe(dto)`, `kiemTraChongLan(maVung, tuNgay, denNgay)`, `ketThucHieuLuc(maHeSo)`, `luu(dto)`

### MoiTruong

**Trách nhiệm:** Môi trường triển khai của sản phẩm (dev, staging, prod), gắn trung tâm dữ liệu (BR07, BR17).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaMoiTruong | string | PK | Có |
| MaSanPham | string | FK → SanPham | Có |
| TenMoiTruong | string |  | Có |
| LoaiMoiTruong | string |  | Có |
| MaTrungTam | string | FK → TrungTamDuLieu | Không |
| CoDongHoDien | bool |  | Có |
| HoatDong | bool |  | Có |

**Phương thức:** `layTatCa()`, `timMoiTruong(maSP, maMT)`, `layTrungTamDuLieu(maMT)`, `trungTen(maSP, tenMT)`, `daCoSoLieu()`, `voHieuHoa()`, `luu(dto)`

### Trang

**Trách nhiệm:** Trang web hoặc màn hình được đo kích thước, hiệu năng.

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaTrang | string | PK | Có |
| MaMoiTruong | string | FK → MoiTruong | Có |
| Url | string |  | Có |

**Phương thức:** `timTheoURL(maMT, url)`, `tao(maMT, url)`

### SoLieuHaTang

**Trách nhiệm:** Số liệu tài nguyên hạ tầng; có cờ công suất thật để chọn Đo hay Ước lượng (BR02, BR09, BR19).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaSoLieu | long | PK | Có |
| MaMoiTruong | string | FK → MoiTruong | Có |
| ThoiDiem | DateTime |  | Có |
| CpuPhanTram | decimal |  | Có |
| RamMB | decimal |  | Có |
| OdiaGB | decimal |  | Có |
| BangThongMB | decimal |  | Có |
| CongSuatW | decimal |  | Không |
| CoCongSuatThat | bool |  | Có |
| TrangThai | string |  | Có |

**Phương thức:** `kiemTraHopLe(diem)`, `danhDauCongSuatThat(diem)`, `luu(diem)`, `layDaChuanHoa()`, `layTrongCuaSo(cuaSo)`, `chuyenDaQuyDoi()`

### SoLieuTrang

**Trách nhiệm:** Số liệu kích thước trang và hiệu năng theo từng lần đo (BR09, BR19).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaSoLieuTrang | long | PK | Có |
| MaTrang | string | FK → Trang | Có |
| ThoiDiem | DateTime |  | Có |
| TongDungLuongKB | decimal |  | Có |
| SoRequest | int |  | Có |
| DungLuongAnhKB | decimal |  | Không |
| DungLuongJsKB | decimal |  | Không |
| DungLuongCssKB | decimal |  | Không |
| TtfbMs | int |  | Có |
| ThoiGianTaiMs | int |  | Có |
| TyLeLoi | decimal |  | Có |

**Phương thức:** `kiemTraHopLe(diem)`, `luu(diem)`, `layTrongCuaSo(cuaSo)`, `tongHopHieuNang(maSP, maMT, ky)`, `gomNhom(maSP, maMT, ky, doChiTiet)`

### KetQuaCarbon

**Trách nhiệm:** Kết quả năng lượng và carbon; luôn mang LoaiDuLieu, DoTinCay, NguonHeSo (BR01-BR08).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaKetQua | long | PK | Có |
| MaSoLieu | long | FK → SoLieuHaTang | Có |
| MaHeSo | string | FK → HeSoPhatThai | Có |
| NangLuongKWh | decimal |  | Có |
| HeSoSuDung | decimal |  | Có |
| CarbonG | decimal |  | Có |
| LoaiDuLieu | string |  | Có |
| DoTinCay | string |  | Có |
| NguonHeSo | string |  | Có |
| CongThuc | string |  | Không |
| ThamSo | string |  | Không |
| DaKiemTraNguong | bool |  | Có |
| ThoiDiemTinh | DateTime |  | Có |

**Phương thức:** `tao(nangLuong, heSo, loaiDuLieu, nguonHeSo)`, `tinhCarbon()`, `xacDinhDoTinCay()`, `layChuaKiemTra()`, `danhDauDaKiemTra()`, `tongHop(maSP, maMT, ky)`, `tongHopKy(ky)`, `tongHopTheoMoiTruong(maSP, ky)`, `gomNhom(maSP, maMT, ky, doChiTiet)`, `layLanCan(maMT, thoiDiem)`

### NguongCanhBao

**Trách nhiệm:** Ngưỡng cảnh báo và mục tiêu giảm tác động.

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaNguong | string | PK | Có |
| MaSanPham | string | FK → SanPham | Có |
| MaMoiTruong | string | FK → MoiTruong | Không |
| ChiTieu | string |  | Có |
| ToanTu | string |  | Có |
| GiaTri | decimal |  | Có |
| DonVi | string |  | Có |
| MucNghiemTrong | string |  | Có |
| MucTieuGiamPhanTram | decimal |  | Không |
| HieuLuc | bool |  | Có |

**Phương thức:** `layTatCa()`, `layNguongHieuLuc(maSP, maMT)`, `vuotNguong(ketQua)`, `kiemTraHopLe(dto)`, `kiemTraTrung(maMT, chiTieu)`, `luu(dto)`, `voHieuHoa()`

### CanhBao

**Trách nhiệm:** Cảnh báo vượt ngưỡng, có vòng đời Mới, Đã xác nhận, Đã đóng (BR10).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaCanhBao | string | PK | Có |
| MaNguong | string | FK → NguongCanhBao | Có |
| MaMoiTruong | string | FK → MoiTruong | Có |
| GiaTriViPham | decimal |  | Có |
| LoaiDuLieu | string |  | Có |
| TrangThai | string |  | Có |
| ThoiDiemTao | DateTime |  | Có |
| ThoiDiemGanNhat | DateTime |  | Có |
| MaNguoiXuLy | string | FK → TaiKhoan | Không |
| GhiChu | string |  | Không |

**Phương thức:** `timChuaDong(maNguong, maMT)`, `tao(nguong, giaTri, loaiDuLieu)`, `capNhatGiaTri(giaTri, thoiDiem)`, `xacNhan(nguoiXuLy)`, `kiemTraGhiChu(ghiChu)`, `dong(ghiChu)`, `demDangMo(maSP, maMT)`, `demDangMoTheoNguong(maNguong)`, `tongHop(maSP, ky)`, `layTheoMa(maCB)`

### LoaiHanhDong

**Trách nhiệm:** Danh mục loại hành động giảm tác động (nén ảnh, bật cache, tắt máy chủ nhàn rỗi, chuyển vùng).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaLoai | string | PK | Có |
| TenLoai | string |  | Có |
| MoTa | string |  | Không |

**Phương thức:** `layLoai(maLoai)`

### HanhDongGiamTacDong

**Trách nhiệm:** Hành động giảm tác động, từ đề xuất đến áp dụng; mức giảm đề xuất luôn là ước lượng (BR20).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaHanhDong | string | PK | Có |
| MaLoai | string | FK → LoaiHanhDong | Có |
| MaMoiTruong | string | FK → MoiTruong | Có |
| Nguon | string |  | Có |
| TrangThai | string |  | Có |
| MucGiamUocTinhKWh | decimal |  | Không |
| MucGiamUocTinhG | decimal |  | Không |
| LyDoTuChoi | string |  | Không |
| NgayApDung | DateTime |  | Không |
| MaNguoiThucHien | string | FK → TaiKhoan | Không |
| ThoiDiemTao | DateTime |  | Có |

**Phương thức:** `tao(loai, mucGiam)`, `daCoHanhDong(loai, maMT)`, `layTheoMa(maHD)`, `chapNhan()`, `tuChoi(lyDo)`, `danhDauDaApDung(ngay)`, `duNgaySauApDung(soNgayToiThieu)`, `tongHop(maSP, ky)`

### DanhGiaHieuQua

**Trách nhiệm:** Kết quả so sánh trước và sau khi áp dụng hành động (BR11, BR12).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaDanhGia | string | PK | Có |
| MaHanhDong | string | FK → HanhDongGiamTacDong | Có |
| TongTruoc | decimal |  | Có |
| TongSau | decimal |  | Có |
| MucGiam | decimal |  | Có |
| TyLeGiam | decimal |  | Có |
| SoNgayMoiKy | int |  | Có |
| LoaiDuLieu | string |  | Có |
| ThoiDiem | DateTime |  | Có |

**Phương thức:** `tao(maHD, tongTruoc, tongSau)`, `tinhMucGiam()`, `xacDinhNhan()`, `luu()`

### BaoCao

**Trách nhiệm:** Báo cáo tổng hợp, luôn kèm tỷ lệ dữ liệu ước lượng và ghi chú phương pháp (BR04).

| Thuộc tính | Kiểu | Khóa | Bắt buộc |
|---|---|---|---|
| MaBaoCao | string | PK | Có |
| LoaiBaoCao | string |  | Có |
| MaSanPham | string | FK → SanPham | Có |
| TuNgay | DateTime |  | Có |
| DenNgay | DateTime |  | Có |
| NoiDung | string |  | Có |
| TyLeUocLuong | decimal |  | Có |
| GhiChuPhuongPhap | string |  | Có |
| MaNguoiLap | string | FK → TaiKhoan | Có |
| ThoiDiem | DateTime |  | Có |

**Phương thức:** `tao(loai, ky, dsCarbon, dsCanhBao, dsHanhDong)`, `ganNhan()`, `tinhTyLeUocLuong()`, `luu()`, `xuat(dinhDang)`

## D. Mô tả chi tiết bảng CSDL (mục 4.2)

### VaiTro

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaVaiTro | NVARCHAR(20) | Không | PK |  |
| TenVaiTro | NVARCHAR(100) | Không |  |  |
| MoTa | NVARCHAR(250) | Có |  |  |

**Ràng buộc:**
- UNIQUE (TenVaiTro)

### TaiKhoan

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaTaiKhoan | NVARCHAR(20) | Không | PK |  |
| TenDangNhap | NVARCHAR(50) | Không |  |  |
| MatKhauBam | NVARCHAR(200) | Không |  |  |
| Salt | NVARCHAR(100) | Không |  |  |
| HoTen | NVARCHAR(100) | Không |  |  |
| Email | NVARCHAR(150) | Không |  |  |
| MaVaiTro | NVARCHAR(20) | Không | FK → VaiTro(MaVaiTro) |  |
| TrangThai | BIT | Không |  | DEFAULT 1 |
| SoLanSai | INT | Không |  | DEFAULT 0 |
| KhoaDen | DATETIME2 | Có |  |  |

**Ràng buộc:**
- UNIQUE (TenDangNhap)
- CHECK: `SoLanSai >= 0`

### PhienLamViec

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaPhien | NVARCHAR(40) | Không | PK |  |
| MaTaiKhoan | NVARCHAR(20) | Không | FK → TaiKhoan(MaTaiKhoan) |  |
| Token | NVARCHAR(200) | Không |  |  |
| ThoiDiemTao | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |
| HanDung | DATETIME2 | Không |  |  |
| HieuLuc | BIT | Không |  | DEFAULT 1 |

**Ràng buộc:**
- UNIQUE (Token)
- CHECK: `HanDung > ThoiDiemTao`

### NhatKyHeThong

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaNhatKy | BIGINT | Không | PK | IDENTITY(1,1) |
| MaTaiKhoan | NVARCHAR(20) | Có | FK → TaiKhoan(MaTaiKhoan) |  |
| HanhDong | NVARCHAR(100) | Không |  |  |
| ChiTiet | NVARCHAR(500) | Có |  |  |
| ThoiDiem | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |

### SanPham

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaSanPham | NVARCHAR(20) | Không | PK |  |
| TenSanPham | NVARCHAR(150) | Không |  |  |
| MoTa | NVARCHAR(500) | Có |  |  |
| LoaiSanPham | NVARCHAR(20) | Không |  |  |
| KhoaAPI | NVARCHAR(100) | Không |  |  |
| TrangThai | NVARCHAR(20) | Không |  | DEFAULT N'DangTheoDoi' |

**Ràng buộc:**
- UNIQUE (KhoaAPI)
- CHECK: `LoaiSanPham IN (N'Web', N'UngDung', N'API')`
- CHECK: `TrangThai IN (N'DangTheoDoi', N'NgungTheoDoi')`

### TaiKhoanSanPham

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaTaiKhoan | NVARCHAR(20) | Không | PK, FK → TaiKhoan(MaTaiKhoan) |  |
| MaSanPham | NVARCHAR(20) | Không | PK, FK → SanPham(MaSanPham) |  |

### VungLuoiDien

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaVung | NVARCHAR(20) | Không | PK |  |
| TenVung | NVARCHAR(100) | Không |  |  |
| QuocGia | NVARCHAR(100) | Không |  |  |

**Ràng buộc:**
- UNIQUE (TenVung)

### TrungTamDuLieu

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaTrungTam | NVARCHAR(20) | Không | PK |  |
| TenTrungTam | NVARCHAR(150) | Không |  |  |
| NhaCungCap | NVARCHAR(100) | Không |  |  |
| MaVung | NVARCHAR(20) | Không | FK → VungLuoiDien(MaVung) |  |
| ViDo | DECIMAL(9,6) | Không |  |  |
| KinhDo | DECIMAL(9,6) | Không |  |  |
| ViTri | geography | Không |  | tính từ ViDo, KinhDo |

**Ràng buộc:**
- CHECK: `ViDo BETWEEN -90 AND 90`
- CHECK: `KinhDo BETWEEN -180 AND 180`

### HeSoPhatThai

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaHeSo | NVARCHAR(20) | Không | PK |  |
| MaVung | NVARCHAR(20) | Không | FK → VungLuoiDien(MaVung) |  |
| GiaTri | DECIMAL(10,2) | Không |  |  |
| Nam | INT | Không |  |  |
| NguonHeSo | NVARCHAR(250) | Không |  |  |
| HieuLucTu | DATE | Không |  |  |
| HieuLucDen | DATE | Có |  |  |
| LaMacDinhQuocGia | BIT | Không |  | DEFAULT 0 |

**Ràng buộc:**
- CHECK: `GiaTri > 0`
- CHECK: `LEN(LTRIM(RTRIM(NguonHeSo))) > 0`
- CHECK: `HieuLucDen IS NULL OR HieuLucDen >= HieuLucTu`

### MoiTruong

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaMoiTruong | NVARCHAR(20) | Không | PK |  |
| MaSanPham | NVARCHAR(20) | Không | FK → SanPham(MaSanPham) |  |
| TenMoiTruong | NVARCHAR(100) | Không |  |  |
| LoaiMoiTruong | NVARCHAR(20) | Không |  |  |
| MaTrungTam | NVARCHAR(20) | Có | FK → TrungTamDuLieu(MaTrungTam) |  |
| CoDongHoDien | BIT | Không |  | DEFAULT 0 |
| HoatDong | BIT | Không |  | DEFAULT 1 |

**Ràng buộc:**
- UNIQUE (MaSanPham, TenMoiTruong)
- CHECK: `LoaiMoiTruong IN (N'dev', N'staging', N'prod')`

### Trang

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaTrang | NVARCHAR(30) | Không | PK |  |
| MaMoiTruong | NVARCHAR(20) | Không | FK → MoiTruong(MaMoiTruong) |  |
| Url | NVARCHAR(400) | Không |  |  |

**Ràng buộc:**
- UNIQUE (MaMoiTruong, Url)

### SoLieuHaTang

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaSoLieu | BIGINT | Không | PK | IDENTITY(1,1) |
| MaMoiTruong | NVARCHAR(20) | Không | FK → MoiTruong(MaMoiTruong) |  |
| ThoiDiem | DATETIME2 | Không |  |  |
| CpuPhanTram | DECIMAL(5,2) | Không |  |  |
| RamMB | DECIMAL(12,2) | Không |  |  |
| OdiaGB | DECIMAL(12,2) | Không |  |  |
| BangThongMB | DECIMAL(14,2) | Không |  |  |
| CongSuatW | DECIMAL(10,2) | Có |  |  |
| CoCongSuatThat | BIT | Không |  |  |
| TrangThai | NVARCHAR(20) | Không |  | DEFAULT N'DaChuanHoa' |

**Ràng buộc:**
- UNIQUE (MaMoiTruong, ThoiDiem)
- CHECK: `CpuPhanTram BETWEEN 0 AND 100`
- CHECK: `RamMB >= 0 AND OdiaGB >= 0 AND BangThongMB >= 0`
- CHECK: `CongSuatW IS NULL OR CongSuatW > 0`
- CHECK: `CoCongSuatThat = CASE WHEN CongSuatW IS NULL THEN 0 ELSE 1 END`
- CHECK: `TrangThai IN (N'DaChuanHoa', N'DaQuyDoi')`

### SoLieuTrang

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaSoLieuTrang | BIGINT | Không | PK | IDENTITY(1,1) |
| MaTrang | NVARCHAR(30) | Không | FK → Trang(MaTrang) |  |
| ThoiDiem | DATETIME2 | Không |  |  |
| TongDungLuongKB | DECIMAL(12,2) | Không |  |  |
| SoRequest | INT | Không |  |  |
| DungLuongAnhKB | DECIMAL(12,2) | Có |  |  |
| DungLuongJsKB | DECIMAL(12,2) | Có |  |  |
| DungLuongCssKB | DECIMAL(12,2) | Có |  |  |
| TtfbMs | INT | Không |  |  |
| ThoiGianTaiMs | INT | Không |  |  |
| TyLeLoi | DECIMAL(5,2) | Không |  |  |

**Ràng buộc:**
- UNIQUE (MaTrang, ThoiDiem)
- CHECK: `TongDungLuongKB >= 0 AND SoRequest >= 0 AND TtfbMs >= 0 AND ThoiGianTaiMs >= 0`
- CHECK: `TyLeLoi BETWEEN 0 AND 100`

### KetQuaCarbon

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaKetQua | BIGINT | Không | PK | IDENTITY(1,1) |
| MaSoLieu | BIGINT | Không | FK → SoLieuHaTang(MaSoLieu) |  |
| MaHeSo | NVARCHAR(20) | Không | FK → HeSoPhatThai(MaHeSo) |  |
| NangLuongKWh | DECIMAL(18,6) | Không |  |  |
| HeSoSuDung | DECIMAL(10,2) | Không |  |  |
| CarbonG | DECIMAL(18,4) | Không |  |  |
| LoaiDuLieu | NVARCHAR(10) | Không |  |  |
| DoTinCay | NVARCHAR(10) | Không |  |  |
| NguonHeSo | NVARCHAR(250) | Không |  |  |
| CongThuc | NVARCHAR(500) | Có |  |  |
| ThamSo | NVARCHAR(500) | Có |  |  |
| DaKiemTraNguong | BIT | Không |  | DEFAULT 0 |
| ThoiDiemTinh | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |

**Ràng buộc:**
- UNIQUE (MaSoLieu)
- CHECK: `LoaiDuLieu IN (N'Do', N'UocLuong')`
- CHECK: `DoTinCay IN (N'Cao', N'TrungBinh', N'Thap')`
- CHECK: `LEN(LTRIM(RTRIM(NguonHeSo))) > 0`
- CHECK: `LoaiDuLieu = N'Do' OR CongThuc IS NOT NULL`
- CHECK: `LoaiDuLieu <> N'Do' OR DoTinCay = N'Cao'`
- CHECK: `NangLuongKWh >= 0 AND CarbonG >= 0`

### NguongCanhBao

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaNguong | NVARCHAR(30) | Không | PK |  |
| MaSanPham | NVARCHAR(20) | Không | FK → SanPham(MaSanPham) |  |
| MaMoiTruong | NVARCHAR(20) | Có | FK → MoiTruong(MaMoiTruong) |  |
| ChiTieu | NVARCHAR(30) | Không |  |  |
| ToanTu | NVARCHAR(5) | Không |  |  |
| GiaTri | DECIMAL(18,4) | Không |  |  |
| DonVi | NVARCHAR(20) | Không |  |  |
| MucNghiemTrong | NVARCHAR(15) | Không |  |  |
| MucTieuGiamPhanTram | DECIMAL(5,2) | Có |  |  |
| HieuLuc | BIT | Không |  | DEFAULT 1 |

**Ràng buộc:**
- CHECK: `ChiTieu IN (N'Carbon', N'NangLuong', N'KichThuocTrang', N'ThoiGianPhanHoi', N'Cpu')`
- CHECK: `ToanTu IN (N'>', N'>=', N'<', N'<=')`
- CHECK: `GiaTri > 0`
- CHECK: `MucNghiemTrong IN (N'Thap', N'TrungBinh', N'Cao')`
- CHECK: `MucTieuGiamPhanTram IS NULL OR (MucTieuGiamPhanTram > 0 AND MucTieuGiamPhanTram <= 100)`

### CanhBao

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaCanhBao | NVARCHAR(40) | Không | PK |  |
| MaNguong | NVARCHAR(30) | Không | FK → NguongCanhBao(MaNguong) |  |
| MaMoiTruong | NVARCHAR(20) | Không | FK → MoiTruong(MaMoiTruong) |  |
| GiaTriViPham | DECIMAL(18,4) | Không |  |  |
| LoaiDuLieu | NVARCHAR(10) | Không |  |  |
| TrangThai | NVARCHAR(15) | Không |  | DEFAULT N'Moi' |
| ThoiDiemTao | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |
| ThoiDiemGanNhat | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |
| MaNguoiXuLy | NVARCHAR(20) | Có | FK → TaiKhoan(MaTaiKhoan) |  |
| GhiChu | NVARCHAR(500) | Có |  |  |

**Ràng buộc:**
- CHECK: `LoaiDuLieu IN (N'Do', N'UocLuong')`
- CHECK: `TrangThai IN (N'Moi', N'DaXacNhan', N'DaDong')`
- CHECK: `TrangThai <> N'DaDong' OR GhiChu IS NOT NULL`

### LoaiHanhDong

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaLoai | NVARCHAR(20) | Không | PK |  |
| TenLoai | NVARCHAR(100) | Không |  |  |
| MoTa | NVARCHAR(250) | Có |  |  |

**Ràng buộc:**
- UNIQUE (TenLoai)

### HanhDongGiamTacDong

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaHanhDong | NVARCHAR(40) | Không | PK |  |
| MaLoai | NVARCHAR(20) | Không | FK → LoaiHanhDong(MaLoai) |  |
| MaMoiTruong | NVARCHAR(20) | Không | FK → MoiTruong(MaMoiTruong) |  |
| Nguon | NVARCHAR(10) | Không |  |  |
| TrangThai | NVARCHAR(15) | Không |  | DEFAULT N'DeXuat' |
| MucGiamUocTinhKWh | DECIMAL(18,6) | Có |  |  |
| MucGiamUocTinhG | DECIMAL(18,4) | Có |  |  |
| LyDoTuChoi | NVARCHAR(250) | Có |  |  |
| NgayApDung | DATE | Có |  |  |
| MaNguoiThucHien | NVARCHAR(20) | Có | FK → TaiKhoan(MaTaiKhoan) |  |
| ThoiDiemTao | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |

**Ràng buộc:**
- CHECK: `Nguon IN (N'DeXuat', N'TuTao')`
- CHECK: `TrangThai IN (N'DeXuat', N'DaChapNhan', N'TuChoi', N'DaApDung')`
- CHECK: `TrangThai <> N'TuChoi' OR LyDoTuChoi IS NOT NULL`
- CHECK: `TrangThai <> N'DaApDung' OR NgayApDung IS NOT NULL`

### DanhGiaHieuQua

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaDanhGia | NVARCHAR(40) | Không | PK |  |
| MaHanhDong | NVARCHAR(40) | Không | FK → HanhDongGiamTacDong(MaHanhDong) |  |
| TongTruoc | DECIMAL(18,4) | Không |  |  |
| TongSau | DECIMAL(18,4) | Không |  |  |
| MucGiam | DECIMAL(18,4) | Không |  |  |
| TyLeGiam | DECIMAL(7,2) | Không |  |  |
| SoNgayMoiKy | INT | Không |  |  |
| LoaiDuLieu | NVARCHAR(10) | Không |  |  |
| ThoiDiem | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |

**Ràng buộc:**
- CHECK: `LoaiDuLieu IN (N'Do', N'UocLuong')`
- CHECK: `SoNgayMoiKy > 0`

### BaoCao

| Cột | Kiểu SQL Server | NULL | Khóa | Ghi chú |
|---|---|---|---|---|
| MaBaoCao | NVARCHAR(40) | Không | PK |  |
| LoaiBaoCao | NVARCHAR(20) | Không |  |  |
| MaSanPham | NVARCHAR(20) | Không | FK → SanPham(MaSanPham) |  |
| TuNgay | DATE | Không |  |  |
| DenNgay | DATE | Không |  |  |
| NoiDung | NVARCHAR(MAX) | Không |  |  |
| TyLeUocLuong | DECIMAL(5,2) | Không |  |  |
| GhiChuPhuongPhap | NVARCHAR(500) | Không |  |  |
| MaNguoiLap | NVARCHAR(20) | Không | FK → TaiKhoan(MaTaiKhoan) |  |
| ThoiDiem | DATETIME2 | Không |  | DEFAULT SYSUTCDATETIME() |

**Ràng buộc:**
- CHECK: `LoaiBaoCao IN (N'Carbon', N'HieuNang', N'CanhBao', N'HanhDong', N'TongHop')`
- CHECK: `DenNgay >= TuNgay`
- CHECK: `TyLeUocLuong BETWEEN 0 AND 100`

## E. Ràng buộc nghiệp vụ được khóa ở CSDL (mục 4.3)

| BR | Cách bảo đảm trong CSDL |
|---|---|
| BR01 | KetQuaCarbon: LoaiDuLieu, DoTinCay, NguonHeSo đều NOT NULL kèm CHECK giá trị hợp lệ |
| BR02 | SoLieuHaTang: CHECK CoCongSuatThat khớp với CongSuatW có hay không |
| BR05 | KetQuaCarbon: CHECK LoaiDuLieu = 'Do' hoặc CongThuc không rỗng |
| BR06, BR07 | MoiTruong.MaTrungTam cho phép NULL; TrungTamDuLieu → VungLuoiDien → HeSoPhatThai |
| BR08 | KetQuaCarbon: CHECK nếu LoaiDuLieu = 'Do' thì DoTinCay = 'Cao' |
| BR09 | SoLieuHaTang, SoLieuTrang: CHECK CPU 0-100, các giá trị không âm, tỷ lệ lỗi 0-100 |
| BR10 | Filtered unique index UX_CanhBao_ChuaDong |
| BR13, BR14 | TaiKhoan: SoLanSai, KhoaDen, MatKhauBam + Salt (xử lý ở service) |
| BR15 | Bảng TaiKhoanSanPham |
| BR16 | SanPham.TrangThai: DangTheoDoi / NgungTheoDoi, không xóa cứng |
| BR17 | MoiTruong: UNIQUE (MaSanPham, TenMoiTruong) |
| BR18 | Trigger TR_HeSoPhatThai_KhongChongLan |
| BR19 | UNIQUE (MaMoiTruong, ThoiDiem) và UNIQUE (MaTrang, ThoiDiem) |
| BR20, BR12 | HanhDongGiamTacDong và DanhGiaHieuQua mang LoaiDuLieu / trạng thái; nhãn lan truyền xử lý ở service |
| BR03, BR04, BR11 | Tính toán và hiển thị, xử lý ở tầng service, không đặt trong CSDL |

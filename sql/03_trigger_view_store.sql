/* =====================================================================
   GreenDash - BỔ SUNG: trigger, view, stored procedure (chạy SAU 01_greendash.sql và 02_sua_do_chinh_xac.sql)
   Chạy toàn bộ file trong SSMS. Chạy lại nhiều lần được (CREATE OR ALTER).
   KHÔNG xóa dữ liệu. Chỉ tạo thêm 1 bảng nhật ký, 7 trigger, 1 view, 2 thủ tục.
   Nếu database của bạn tên khác GreenDashDB thì sửa dòng USE bên dưới.
   ===================================================================== */
USE GreenDashDB;
GO

/* ---------------------------------------------------------------------
   0. Bảng nhật ký (trigger TR_CanhBao_GhiNhatKy ghi vào đây). Chỉ ghi thêm, không sửa.
   --------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.NhatKyHeThong', N'U') IS NULL
CREATE TABLE dbo.NhatKyHeThong (
    MaNhatKy       BIGINT IDENTITY PRIMARY KEY,
    ThoiDiem       DATETIME2(0)  NOT NULL CONSTRAINT DF_NK_TD DEFAULT SYSUTCDATETIME(),   -- UTC
    Bang           NVARCHAR(50)  NOT NULL,
    MaDoiTuong     NVARCHAR(50)  NOT NULL,
    HanhDong       NVARCHAR(50)  NOT NULL,
    GiaTriCu       NVARCHAR(100) NULL,
    GiaTriMoi      NVARCHAR(100) NULL,
    NguoiThucHien  NVARCHAR(128) NOT NULL CONSTRAINT DF_NK_NG DEFAULT SUSER_SNAME()
);
GO

/* =====================================================================
   1. TRIGGER
   Quy ước: trigger chạy MỘT LẦN cho cả câu lệnh, nên luôn viết theo tập hợp (JOIN/EXISTS với inserted, deleted).
   Muốn chặn: ROLLBACK TRANSACTION rồi RAISERROR (mã lỗi 50000).
   ===================================================================== */

/* 1.1 Không cho SỬA kết quả carbon đã tính (BR: kết quả phải truy vết được).
       Chỉ cho đổi cột DaKiemTraNguong, vì usp_GhiNhanCanhBao cần đánh dấu "đã kiểm tra ngưỡng". */
CREATE OR ALTER TRIGGER dbo.TR_KetQuaCarbon_ChanSua ON dbo.KetQuaCarbon AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i JOIN deleted d ON d.MaKetQua = i.MaKetQua
        WHERE i.MaSoLieu <> d.MaSoLieu OR i.NangLuongKWh <> d.NangLuongKWh OR i.CarbonG <> d.CarbonG
           OR i.HeSoKgKwh <> d.HeSoKgKwh OR i.LoaiDuLieu <> d.LoaiDuLieu OR i.DoTinCay <> d.DoTinCay
           OR i.NguonHeSo <> d.NguonHeSo
           OR ISNULL(i.CongThuc, N'') <> ISNULL(d.CongThuc, N'') OR ISNULL(i.ThamSo, N'') <> ISNULL(d.ThamSo, N''))
    BEGIN
        ROLLBACK TRANSACTION;
        RAISERROR(N'Kết quả carbon đã tính không được sửa. Chỉ được đổi cờ DaKiemTraNguong.', 16, 1);
    END
END;
GO

/* 1.2 Không cho XÓA kết quả carbon. */
CREATE OR ALTER TRIGGER dbo.TR_KetQuaCarbon_ChanXoa ON dbo.KetQuaCarbon AFTER DELETE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted)
    BEGIN
        ROLLBACK TRANSACTION;
        RAISERROR(N'Không được xóa kết quả carbon đã tính.', 16, 1);
    END
END;
GO

/* 1.3 Có kết quả carbon thì tự chuyển số liệu hạ tầng sang DaQuyDoi (đồng bộ trạng thái). */
CREATE OR ALTER TRIGGER dbo.TR_KetQuaCarbon_DongBoTrangThai ON dbo.KetQuaCarbon AFTER INSERT AS
BEGIN
    SET NOCOUNT ON;
    UPDATE s SET TrangThai = N'DaQuyDoi'
    FROM dbo.SoLieuHaTang s
    JOIN inserted i ON i.MaSoLieu = s.MaSoLieu
    WHERE s.TrangThai <> N'DaQuyDoi';
END;
GO

/* 1.4 Cảnh báo đã đóng không được mở lại (BR10 mở rộng). */
CREATE OR ALTER TRIGGER dbo.TR_CanhBao_KhongMoLai ON dbo.CanhBao AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted d JOIN inserted i ON i.MaCanhBao = d.MaCanhBao
               WHERE d.TrangThai = N'DaDong' AND i.TrangThai <> N'DaDong')
    BEGIN
        ROLLBACK TRANSACTION;
        RAISERROR(N'Cảnh báo đã đóng không được mở lại.', 16, 1);
    END
END;
GO

/* 1.5 Đổi trạng thái cảnh báo thì tự ghi nhật ký (dùng cả inserted lẫn deleted). */
CREATE OR ALTER TRIGGER dbo.TR_CanhBao_GhiNhatKy ON dbo.CanhBao AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(TrangThai) RETURN;                 -- lệnh UPDATE không đụng cột TrangThai thì bỏ qua
    INSERT INTO dbo.NhatKyHeThong (Bang, MaDoiTuong, HanhDong, GiaTriCu, GiaTriMoi)
    SELECT N'CanhBao', CAST(i.MaCanhBao AS NVARCHAR(50)), N'DoiTrangThai', d.TrangThai, i.TrangThai
    FROM inserted i JOIN deleted d ON d.MaCanhBao = i.MaCanhBao
    WHERE i.TrangThai <> d.TrangThai;
END;
GO

/* 1.6 Hành động đã áp dụng không được lùi về trạng thái trước (bài tập 3 trong tài liệu). */
CREATE OR ALTER TRIGGER dbo.TR_HanhDong_KhongLuiTrangThai ON dbo.HanhDong AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted d JOIN inserted i ON i.MaHanhDong = d.MaHanhDong
               WHERE d.TrangThai = N'DaApDung' AND i.TrangThai <> N'DaApDung')
    BEGIN
        ROLLBACK TRANSACTION;
        RAISERROR(N'Hành động đã áp dụng không được quay lại trạng thái trước.', 16, 1);
    END
END;
GO

/* 1.7 INSTEAD OF DELETE: xóa sản phẩm thì chỉ đánh dấu "Ngừng theo dõi" (giữ nguyên lịch sử số liệu). */
CREATE OR ALTER TRIGGER dbo.TR_SanPham_KhongXoaCung ON dbo.SanPham INSTEAD OF DELETE AS
BEGIN
    SET NOCOUNT ON;
    UPDATE sp SET TrangThai = N'NgungTheoDoi'
    FROM dbo.SanPham sp
    JOIN deleted d ON d.MaSanPham = sp.MaSanPham;
END;
GO

/* =====================================================================
   2. VIEW mới: tổng hợp carbon theo sản phẩm và THÁNG, kèm nhãn tổng gộp (BR12)
   ===================================================================== */
CREATE OR ALTER VIEW dbo.vw_CarbonTheoSanPhamThang AS
SELECT  mt.MaSanPham,
        YEAR(s.ThoiDiem)   AS Nam,
        MONTH(s.ThoiDiem)  AS Thang,
        SUM(k.NangLuongKWh) AS NangLuongKWh,
        SUM(k.CarbonG)      AS CarbonG,
        COUNT(*)            AS SoDiem,
        CASE WHEN SUM(CASE WHEN k.LoaiDuLieu = N'UocLuong' THEN 1 ELSE 0 END) = 0 THEN N'Do'
             WHEN SUM(CASE WHEN k.LoaiDuLieu = N'Do'       THEN 1 ELSE 0 END) = 0 THEN N'UocLuong'
             ELSE N'UocLuongMotPhan' END AS NhanTongHop
FROM dbo.KetQuaCarbon k
JOIN dbo.SoLieuHaTang s ON s.MaSoLieu = k.MaSoLieu
JOIN dbo.MoiTruong mt   ON mt.MaMoiTruong = s.MaMoiTruong
GROUP BY mt.MaSanPham, YEAR(s.ThoiDiem), MONTH(s.ThoiDiem);
GO

/* =====================================================================
   3. STORED PROCEDURE mới
   ===================================================================== */

/* 3.1 Các trang nặng nhất của một sản phẩm trong N ngày gần đây (bài tập 2 trong tài liệu). */
CREATE OR ALTER PROCEDURE dbo.usp_TopTrangNang
    @MaSanPham NVARCHAR(20),
    @Top       INT = 5,
    @SoNgay    INT = 7
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.SanPham WHERE MaSanPham = @MaSanPham)
        THROW 50001, N'Không tìm thấy sản phẩm.', 1;
    IF @Top < 1 OR @SoNgay < 1
        THROW 50002, N'Top và SoNgay phải lớn hơn 0.', 1;

    SELECT TOP (@Top)
           t.Url,
           COUNT(*)                        AS SoLanDo,
           AVG(v.TongKB)                   AS TongKBTrungBinh,
           AVG(v.SoRequest * 1.0)          AS SoRequestTrungBinh,
           AVG(v.TtfbMs)                   AS TtfbMsTrungBinh
    FROM dbo.SoLieuTrang v
    JOIN dbo.Trang t ON t.MaTrang = v.MaTrang
    WHERE t.MaSanPham = @MaSanPham
      AND v.ThoiDiem >= DATEADD(DAY, -@SoNgay, SYSUTCDATETIME())
    GROUP BY t.Url
    ORDER BY AVG(v.TongKB) DESC;
END;
GO

/* 3.2 Báo cáo tổng hợp carbon theo ngày cho một sản phẩm (gọi view, kiểm tra đầu vào, trả bảng kết quả). */
CREATE OR ALTER PROCEDURE dbo.usp_BaoCaoTongHop
    @MaSanPham NVARCHAR(20),
    @SoNgay    INT = 30
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.SanPham WHERE MaSanPham = @MaSanPham)
        THROW 50001, N'Không tìm thấy sản phẩm.', 1;
    IF @SoNgay < 1 OR @SoNgay > 365
        THROW 50003, N'SoNgay phải từ 1 đến 365.', 1;

    SELECT Ngay, NangLuongKWh, CarbonG, SoDiem, NhanTongHop, DoTinCayThapNhat, NguonHeSo
    FROM dbo.vw_TongHopCarbonNgay
    WHERE MaSanPham = @MaSanPham
      AND Ngay >= CAST(DATEADD(DAY, -@SoNgay, SYSUTCDATETIME()) AS DATE)
    ORDER BY Ngay;
END;
GO

/* =====================================================================
   4. Kiểm tra đã tạo xong
   ===================================================================== */
SELECT name AS TenTrigger, OBJECT_NAME(parent_id) AS TrenBang, is_instead_of_trigger AS LaInsteadOf, is_disabled AS DangTat
FROM sys.triggers WHERE parent_class = 1 ORDER BY name;
SELECT name AS TenView      FROM sys.views      ORDER BY name;
SELECT name AS TenThuTuc    FROM sys.procedures ORDER BY name;
PRINT N'Đã tạo xong trigger, view, thủ tục bổ sung.';
GO

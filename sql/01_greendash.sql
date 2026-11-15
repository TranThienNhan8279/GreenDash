/* =====================================================================
   GreenDash - CSDL SQL Server (2016 trở lên). Chạy toàn bộ file trong SSMS.
   CẢNH BÁO: file này XÓA và tạo lại các bảng GreenDash.
   Quy ước: mọi thời điểm lưu theo UTC.
   ===================================================================== */
IF DB_ID(N'GreenDashDB') IS NULL CREATE DATABASE GreenDashDB;
GO
USE GreenDashDB;
GO

DROP VIEW IF EXISTS dbo.vw_TongHopCarbonNgay;
DROP VIEW IF EXISTS dbo.vw_HieuNangTrang;
DROP VIEW IF EXISTS dbo.vw_CanhBaoDangMo;
DROP TABLE IF EXISTS dbo.CanhBao;
DROP TABLE IF EXISTS dbo.NguongCanhBao;
DROP TABLE IF EXISTS dbo.HanhDong;
DROP TABLE IF EXISTS dbo.KetQuaCarbon;
DROP TABLE IF EXISTS dbo.SoLieuHaTang;
DROP TABLE IF EXISTS dbo.SoLieuTrang;
DROP TABLE IF EXISTS dbo.Trang;
DROP TABLE IF EXISTS dbo.HeSoPhatThai;
DROP TABLE IF EXISTS dbo.TaiKhoanSanPham;
DROP TABLE IF EXISTS dbo.TaiKhoan;
DROP TABLE IF EXISTS dbo.MoiTruong;
DROP TABLE IF EXISTS dbo.SanPham;
DROP TABLE IF EXISTS dbo.VungLuoiDien;
GO

/* ---------- Danh mục nền ---------- */
CREATE TABLE dbo.VungLuoiDien (
    MaVung   NVARCHAR(20)  NOT NULL PRIMARY KEY,
    TenVung  NVARCHAR(100) NOT NULL
);

CREATE TABLE dbo.SanPham (
    MaSanPham   NVARCHAR(20)  NOT NULL PRIMARY KEY,
    TenSanPham  NVARCHAR(150) NOT NULL,
    KhoaApiBam  CHAR(64)      NOT NULL UNIQUE,      -- SHA-256 của khóa API, KHÔNG lưu khóa thô
    TrangThai   NVARCHAR(20)  NOT NULL CONSTRAINT DF_SP_TT DEFAULT N'DangTheoDoi'
                CONSTRAINT CK_SP_TT CHECK (TrangThai IN (N'DangTheoDoi', N'NgungTheoDoi'))
);

CREATE TABLE dbo.MoiTruong (
    MaMoiTruong   NVARCHAR(20)  NOT NULL PRIMARY KEY,
    MaSanPham     NVARCHAR(20)  NOT NULL CONSTRAINT FK_MT_SP REFERENCES dbo.SanPham(MaSanPham),
    TenMoiTruong  NVARCHAR(100) NOT NULL,
    MaVung        NVARCHAR(20)  NULL CONSTRAINT FK_MT_Vung REFERENCES dbo.VungLuoiDien(MaVung),
    -- Tham số mô hình ước lượng công suất: P(W) = CongSuatNenW + HeSoWTheoCpu * %CPU
    -- Giá trị mặc định chỉ là điểm khởi đầu; PHẢI hiệu chỉnh bằng thiết bị đo watt nếu có.
    CongSuatNenW  DECIMAL(9,2)  NOT NULL CONSTRAINT DF_MT_Nen DEFAULT 30 CONSTRAINT CK_MT_Nen CHECK (CongSuatNenW >= 0),
    HeSoWTheoCpu  DECIMAL(9,4)  NOT NULL CONSTRAINT DF_MT_K   DEFAULT 0.7 CONSTRAINT CK_MT_K CHECK (HeSoWTheoCpu >= 0),
    CONSTRAINT UQ_MT_Ten UNIQUE (MaSanPham, TenMoiTruong)
);

CREATE TABLE dbo.TaiKhoan (
    MaTaiKhoan   INT IDENTITY PRIMARY KEY,
    TenDangNhap  NVARCHAR(50)  NOT NULL UNIQUE,
    MatKhauBam   NVARCHAR(200) NOT NULL,            -- bcrypt (đã gồm salt)
    SoLanSai     INT           NOT NULL CONSTRAINT DF_TK_Sai DEFAULT 0,
    KhoaDen      DATETIME2(0)  NULL,
    HoatDong     BIT           NOT NULL CONSTRAINT DF_TK_HD DEFAULT 1
);

CREATE TABLE dbo.TaiKhoanSanPham (
    MaTaiKhoan INT          NOT NULL REFERENCES dbo.TaiKhoan(MaTaiKhoan),
    MaSanPham  NVARCHAR(20) NOT NULL REFERENCES dbo.SanPham(MaSanPham),
    PRIMARY KEY (MaTaiKhoan, MaSanPham)
);

CREATE TABLE dbo.HeSoPhatThai (
    MaHeSo            INT IDENTITY PRIMARY KEY,
    MaVung            NVARCHAR(20)  NULL REFERENCES dbo.VungLuoiDien(MaVung),
    LaMacDinhQuocGia  BIT           NOT NULL CONSTRAINT DF_HS_MD DEFAULT 0,
    HeSoKgKwh         DECIMAL(10,5) NOT NULL CONSTRAINT CK_HS_Duong CHECK (HeSoKgKwh > 0),  -- kg CO2e / kWh
    NguonHeSo         NVARCHAR(300) NOT NULL,       -- tên nguồn, năm, đơn vị
    HieuLucTu         DATE          NOT NULL,
    HieuLucDen        DATE          NULL,
    CONSTRAINT CK_HS_Vung CHECK (LaMacDinhQuocGia = 1 OR MaVung IS NOT NULL),
    CONSTRAINT CK_HS_Ngay CHECK (HieuLucDen IS NULL OR HieuLucDen >= HieuLucTu)
);

/* ---------- Số liệu ---------- */
CREATE TABLE dbo.SoLieuHaTang (
    MaSoLieu     BIGINT IDENTITY PRIMARY KEY,
    MaMoiTruong  NVARCHAR(20)  NOT NULL REFERENCES dbo.MoiTruong(MaMoiTruong),
    ThoiDiem     DATETIME2(0)  NOT NULL,                                   -- UTC, làm tròn phút
    CpuPhanTram  DECIMAL(5,2)  NOT NULL CONSTRAINT CK_SL_Cpu  CHECK (CpuPhanTram BETWEEN 0 AND 100),   -- BR09
    RamMB        DECIMAL(12,2) NOT NULL CONSTRAINT CK_SL_Ram  CHECK (RamMB >= 0),
    OdiaGB       DECIMAL(12,2) NOT NULL CONSTRAINT CK_SL_Odia CHECK (OdiaGB >= 0),
    BangThongMB  DECIMAL(14,2) NOT NULL CONSTRAINT CK_SL_BT   CHECK (BangThongMB >= 0),
    CongSuatW    DECIMAL(10,2) NULL     CONSTRAINT CK_SL_W    CHECK (CongSuatW IS NULL OR CongSuatW > 0),  -- NULL = không có watt thật
    TrangThai    NVARCHAR(20)  NOT NULL CONSTRAINT DF_SL_TT DEFAULT N'DaChuanHoa'
                 CONSTRAINT CK_SL_TT CHECK (TrangThai IN (N'DaChuanHoa', N'DaQuyDoi')),
    CONSTRAINT UQ_SL_MT_TD UNIQUE (MaMoiTruong, ThoiDiem)                  -- BR19: chống trùng
);

CREATE TABLE dbo.Trang (
    MaTrang    INT IDENTITY PRIMARY KEY,
    MaSanPham  NVARCHAR(20)  NOT NULL REFERENCES dbo.SanPham(MaSanPham),
    Url        NVARCHAR(400) NOT NULL,
    CONSTRAINT UQ_Trang UNIQUE (MaSanPham, Url)
);

CREATE TABLE dbo.SoLieuTrang (
    MaSoLieuTrang BIGINT IDENTITY PRIMARY KEY,
    MaTrang       INT           NOT NULL REFERENCES dbo.Trang(MaTrang),
    ThoiDiem      DATETIME2(0)  NOT NULL,
    TongKB        DECIMAL(12,2) NOT NULL CHECK (TongKB >= 0),
    SoRequest     INT           NOT NULL CHECK (SoRequest >= 0),
    AnhKB         DECIMAL(12,2) NOT NULL CHECK (AnhKB >= 0),
    JsKB          DECIMAL(12,2) NOT NULL CHECK (JsKB >= 0),
    CssKB         DECIMAL(12,2) NOT NULL CHECK (CssKB >= 0),
    TtfbMs        DECIMAL(10,2) NOT NULL CHECK (TtfbMs >= 0),
    TaiMs         DECIMAL(10,2) NOT NULL CHECK (TaiMs >= 0),
    TyLeLoi       DECIMAL(5,2)  NOT NULL CHECK (TyLeLoi BETWEEN 0 AND 100)
);

/* ---------- Kết quả carbon (luôn kèm nhãn) ---------- */
CREATE TABLE dbo.KetQuaCarbon (
    MaKetQua         BIGINT IDENTITY PRIMARY KEY,
    MaSoLieu         BIGINT         NOT NULL UNIQUE REFERENCES dbo.SoLieuHaTang(MaSoLieu),
    NangLuongKWh     DECIMAL(18,8)  NOT NULL,
    CarbonG          DECIMAL(18,6)  NOT NULL,                              -- gam CO2e
    HeSoKgKwh        DECIMAL(10,5)  NOT NULL,
    LoaiDuLieu       NVARCHAR(10)   NOT NULL CONSTRAINT CK_KQ_Loai CHECK (LoaiDuLieu IN (N'Do', N'UocLuong')),
    DoTinCay         NVARCHAR(10)   NOT NULL CONSTRAINT CK_KQ_TC   CHECK (DoTinCay IN (N'Cao', N'TrungBinh', N'Thap')),
    NguonHeSo        NVARCHAR(300)  NOT NULL,
    CongThuc         NVARCHAR(300)  NULL,
    ThamSo           NVARCHAR(300)  NULL,
    DaKiemTraNguong  BIT            NOT NULL CONSTRAINT DF_KQ_KT DEFAULT 0,
    CONSTRAINT CK_KQ_TruyVet CHECK (LoaiDuLieu = N'Do' OR CongThuc IS NOT NULL),     -- BR05
    CONSTRAINT CK_KQ_Do      CHECK (LoaiDuLieu <> N'Do' OR DoTinCay = N'Cao')        -- BR08
);

/* ---------- Cảnh báo, hành động ---------- */
CREATE TABLE dbo.NguongCanhBao (
    MaNguong   INT IDENTITY PRIMARY KEY,
    MaSanPham  NVARCHAR(20)  NOT NULL REFERENCES dbo.SanPham(MaSanPham),
    ChiTieu    NVARCHAR(20)  NOT NULL CHECK (ChiTieu IN (N'Cpu', N'Carbon')),  -- Cpu: TB 1 giờ (%); Carbon: tổng 24 giờ (g)
    ToanTu     CHAR(1)       NOT NULL CHECK (ToanTu IN ('>', '<')),
    GiaTri     DECIMAL(18,4) NOT NULL,
    MoTa       NVARCHAR(200) NULL,
    HoatDong   BIT           NOT NULL DEFAULT 1
);

CREATE TABLE dbo.CanhBao (
    MaCanhBao        INT IDENTITY PRIMARY KEY,
    MaNguong         INT           NOT NULL REFERENCES dbo.NguongCanhBao(MaNguong),
    MaMoiTruong      NVARCHAR(20)  NOT NULL REFERENCES dbo.MoiTruong(MaMoiTruong),
    GiaTriGanNhat    DECIMAL(18,4) NOT NULL,
    ThoiDiemMo       DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
    ThoiDiemGanNhat  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
    TrangThai        NVARCHAR(20)  NOT NULL DEFAULT N'Mo' CHECK (TrangThai IN (N'Mo', N'DaXacNhan', N'DaDong')),
    GhiChuDong       NVARCHAR(300) NULL
);
-- BR10: mỗi (ngưỡng, môi trường) chỉ có một cảnh báo chưa đóng
CREATE UNIQUE INDEX UX_CanhBao_Mo ON dbo.CanhBao(MaNguong, MaMoiTruong) WHERE TrangThai <> N'DaDong';

CREATE TABLE dbo.HanhDong (
    MaHanhDong    INT IDENTITY PRIMARY KEY,
    MaSanPham     NVARCHAR(20)  NOT NULL REFERENCES dbo.SanPham(MaSanPham),
    Loai          NVARCHAR(50)  NOT NULL,
    MoTa          NVARCHAR(500) NOT NULL,
    TrangThai     NVARCHAR(20)  NOT NULL DEFAULT N'DeXuat'
                  CHECK (TrangThai IN (N'DeXuat', N'DaChapNhan', N'TuChoi', N'DaApDung')),
    LoaiMucGiam   NVARCHAR(20)  NOT NULL DEFAULT N'UocLuong',         -- mức giảm đề xuất luôn là Ước lượng
    NgayTao       DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
    NgayApDung    DATE          NULL
);
GO

/* ---------- View ---------- */
CREATE VIEW dbo.vw_TongHopCarbonNgay AS
SELECT  mt.MaSanPham,
        CAST(s.ThoiDiem AS DATE)             AS Ngay,
        SUM(k.NangLuongKWh)                  AS NangLuongKWh,
        SUM(k.CarbonG)                       AS CarbonG,
        COUNT(*)                             AS SoDiem,
        CASE WHEN SUM(CASE WHEN k.LoaiDuLieu = N'UocLuong' THEN 1 ELSE 0 END) = 0 THEN N'Do'
             WHEN SUM(CASE WHEN k.LoaiDuLieu = N'Do'       THEN 1 ELSE 0 END) = 0 THEN N'UocLuong'
             ELSE N'UocLuongMotPhan' END     AS NhanTongHop,                 -- BR12
        CASE WHEN SUM(CASE WHEN k.DoTinCay = N'Thap'      THEN 1 ELSE 0 END) > 0 THEN N'Thap'
             WHEN SUM(CASE WHEN k.DoTinCay = N'TrungBinh' THEN 1 ELSE 0 END) > 0 THEN N'TrungBinh'
             ELSE N'Cao' END                 AS DoTinCayThapNhat,
        MIN(k.NguonHeSo)                     AS NguonHeSo,
        COUNT(DISTINCT k.NguonHeSo)          AS SoNguonHeSo
FROM dbo.KetQuaCarbon k
JOIN dbo.SoLieuHaTang s ON s.MaSoLieu = k.MaSoLieu
JOIN dbo.MoiTruong mt   ON mt.MaMoiTruong = s.MaMoiTruong
GROUP BY mt.MaSanPham, CAST(s.ThoiDiem AS DATE);
GO

CREATE VIEW dbo.vw_HieuNangTrang AS
SELECT  t.MaSanPham, t.Url,
        COUNT(*)            AS SoLanDo,
        AVG(v.TongKB)       AS TongKBTrungBinh,
        AVG(v.SoRequest * 1.0) AS SoRequestTrungBinh,
        AVG(v.AnhKB)        AS AnhKBTrungBinh,
        AVG(v.JsKB)         AS JsKBTrungBinh,
        AVG(v.CssKB)        AS CssKBTrungBinh,
        AVG(v.TtfbMs)       AS TtfbMsTrungBinh,
        AVG(v.TaiMs)        AS TaiMsTrungBinh,
        AVG(v.TyLeLoi)      AS TyLeLoiTrungBinh,
        MAX(v.ThoiDiem)     AS LanDoCuoi
FROM dbo.SoLieuTrang v
JOIN dbo.Trang t ON t.MaTrang = v.MaTrang
WHERE v.ThoiDiem >= DATEADD(DAY, -7, SYSUTCDATETIME())
GROUP BY t.MaSanPham, t.Url;
GO

CREATE VIEW dbo.vw_CanhBaoDangMo AS
SELECT  c.MaCanhBao, n.MaSanPham, c.MaMoiTruong, n.ChiTieu, n.ToanTu, n.GiaTri AS Nguong,
        c.GiaTriGanNhat, c.ThoiDiemMo, c.ThoiDiemGanNhat, c.TrangThai, n.MoTa
FROM dbo.CanhBao c
JOIN dbo.NguongCanhBao n ON n.MaNguong = c.MaNguong
WHERE c.TrangThai <> N'DaDong';
GO

/* ---------- Thủ tục: quy đổi carbon ----------
   P(W)   = công suất thật nếu có, nếu không = nền + k * %CPU
   kWh    = P * (giây/3600) / 1000
   gam    = kWh * hệ số(kg/kWh) * 1000
   Hệ số: đúng vùng còn hiệu lực -> mặc định quốc gia -> không có thì BỎ QUA (không công bố carbon).
*/
CREATE OR ALTER PROCEDURE dbo.usp_QuyDoiCarbon
    @GiayMoiDiem INT = 60
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRAN;

        INSERT INTO dbo.KetQuaCarbon
            (MaSoLieu, NangLuongKWh, CarbonG, HeSoKgKwh, LoaiDuLieu, DoTinCay, NguonHeSo, CongThuc, ThamSo)
        SELECT  s.MaSoLieu,
                c.kWh,
                c.kWh * h.HeSoKgKwh * 1000.0,
                h.HeSoKgKwh,
                CASE WHEN s.CongSuatW IS NOT NULL THEN N'Do' ELSE N'UocLuong' END,
                CASE WHEN s.CongSuatW IS NOT NULL THEN N'Cao'
                     WHEN h.LaMacDinhQuocGia = 1  THEN N'Thap'
                     ELSE N'TrungBinh' END,
                h.NguonHeSo,
                CASE WHEN s.CongSuatW IS NULL
                     THEN N'P = nen + k*CPU; kWh = P*giay/3600/1000; gam = kWh*heso*1000' END,
                CASE WHEN s.CongSuatW IS NULL
                     THEN CONCAT(N'nen=', m.CongSuatNenW, N'W; k=', m.HeSoWTheoCpu, N'W/%CPU; cpu=',
                                 s.CpuPhanTram, N'%; chuky=', @GiayMoiDiem, N's') END
        FROM dbo.SoLieuHaTang s
        JOIN dbo.MoiTruong m ON m.MaMoiTruong = s.MaMoiTruong
        CROSS APPLY (
            SELECT TOP 1 x.HeSoKgKwh, x.NguonHeSo, x.LaMacDinhQuocGia
            FROM dbo.HeSoPhatThai x
            WHERE (x.MaVung = m.MaVung OR x.LaMacDinhQuocGia = 1)
              AND CAST(s.ThoiDiem AS DATE) >= x.HieuLucTu
              AND (x.HieuLucDen IS NULL OR CAST(s.ThoiDiem AS DATE) <= x.HieuLucDen)
            ORDER BY CASE WHEN x.MaVung = m.MaVung THEN 0 ELSE 1 END, x.HieuLucTu DESC
        ) h
        CROSS APPLY (
            SELECT (COALESCE(s.CongSuatW, m.CongSuatNenW + m.HeSoWTheoCpu * s.CpuPhanTram)
                    * (@GiayMoiDiem / 3600.0)) / 1000.0 AS kWh
        ) c
        WHERE s.TrangThai = N'DaChuanHoa';

        DECLARE @SoDong INT = @@ROWCOUNT;   -- lấy ngay sau INSERT

        UPDATE s SET TrangThai = N'DaQuyDoi'
        FROM dbo.SoLieuHaTang s
        WHERE s.TrangThai = N'DaChuanHoa'
          AND EXISTS (SELECT 1 FROM dbo.KetQuaCarbon k WHERE k.MaSoLieu = s.MaSoLieu);

        COMMIT;
        SELECT @SoDong AS SoDongQuyDoi;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        THROW;
    END CATCH
END;
GO

/* ---------- Thủ tục: ghi nhận cảnh báo ---------- */
CREATE OR ALTER PROCEDURE dbo.usp_GhiNhanCanhBao
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRAN;

        ;WITH v AS (
            SELECT n.MaNguong, m.MaMoiTruong, n.ToanTu, n.GiaTri,
                   CASE n.ChiTieu
                     WHEN N'Cpu' THEN
                        (SELECT AVG(x.CpuPhanTram) FROM dbo.SoLieuHaTang x
                         WHERE x.MaMoiTruong = m.MaMoiTruong
                           AND x.ThoiDiem >= DATEADD(HOUR, -1, SYSUTCDATETIME()))
                     WHEN N'Carbon' THEN
                        (SELECT SUM(k.CarbonG) FROM dbo.KetQuaCarbon k
                         JOIN dbo.SoLieuHaTang x ON x.MaSoLieu = k.MaSoLieu
                         WHERE x.MaMoiTruong = m.MaMoiTruong
                           AND x.ThoiDiem >= DATEADD(HOUR, -24, SYSUTCDATETIME()))
                   END AS GiaTriDo
            FROM dbo.NguongCanhBao n
            JOIN dbo.MoiTruong m ON m.MaSanPham = n.MaSanPham
            WHERE n.HoatDong = 1
        )
        SELECT MaNguong, MaMoiTruong, CAST(GiaTriDo AS DECIMAL(18,4)) AS GiaTriDo
        INTO #vipham
        FROM v
        WHERE GiaTriDo IS NOT NULL
          AND ((ToanTu = '>' AND GiaTriDo > GiaTri) OR (ToanTu = '<' AND GiaTriDo < GiaTri));

        UPDATE c SET GiaTriGanNhat = p.GiaTriDo, ThoiDiemGanNhat = SYSUTCDATETIME()
        FROM dbo.CanhBao c
        JOIN #vipham p ON p.MaNguong = c.MaNguong AND p.MaMoiTruong = c.MaMoiTruong
        WHERE c.TrangThai <> N'DaDong';

        INSERT INTO dbo.CanhBao (MaNguong, MaMoiTruong, GiaTriGanNhat)
        SELECT p.MaNguong, p.MaMoiTruong, p.GiaTriDo
        FROM #vipham p
        WHERE NOT EXISTS (SELECT 1 FROM dbo.CanhBao c
                          WHERE c.MaNguong = p.MaNguong AND c.MaMoiTruong = p.MaMoiTruong
                            AND c.TrangThai <> N'DaDong');
        DECLARE @SoMoi INT = @@ROWCOUNT;

        UPDATE dbo.KetQuaCarbon SET DaKiemTraNguong = 1 WHERE DaKiemTraNguong = 0;

        COMMIT;
        SELECT @SoMoi AS SoCanhBaoMoi;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        THROW;
    END CATCH
END;
GO

/* ---------- Vùng lưới điện và hệ số phát thải ----------
   KHÔNG có số liệu mẫu ở đây. Bạn phải tự nhập hệ số THẬT, ghi rõ nguồn và năm.
   Dùng tools/khoi_tao.py --he-so ... --nguon "...", hoặc chạy INSERT mẫu dưới đây sau khi thay giá trị:

   INSERT INTO dbo.HeSoPhatThai (MaVung, LaMacDinhQuocGia, HeSoKgKwh, NguonHeSo, HieuLucTu)
   VALUES (NULL, 1, <số kg CO2e/kWh>, N'<tên nguồn, năm, đơn vị>', '<yyyy-mm-dd>');
*/
INSERT INTO dbo.VungLuoiDien (MaVung, TenVung) VALUES (N'VN', N'Lưới điện quốc gia Việt Nam');
GO

PRINT N'Đã tạo xong GreenDashDB.';

USE GreenDashDB;
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
            SELECT CAST(COALESCE(s.CongSuatW, m.CongSuatNenW + m.HeSoWTheoCpu * s.CpuPhanTram) AS FLOAT)
                   * @GiayMoiDiem / 3600.0 / 1000.0 AS kWh     -- FLOAT để không bị cắt chữ số thập phân
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


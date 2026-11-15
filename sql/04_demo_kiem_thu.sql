/* =====================================================================
   GreenDash - KIỂM THỬ TỰ ĐỘNG cho trigger / view / stored procedure
   Chạy SAU 03_trigger_view_store.sql. Chạy toàn bộ file một lần (F5) rồi xem bảng PASS/FAIL ở cuối.
   AN TOÀN: mọi dữ liệu thử nằm trong BEGIN TRAN ... ROLLBACK, không làm bẩn dữ liệu thật.
   (Các mã T_SP, T_MT chỉ tồn tại trong giao dịch thử rồi bị hoàn tác.)
   ===================================================================== */
USE GreenDashDB;
GO
SET NOCOUNT ON;
DECLARE @kq TABLE (Test NVARCHAR(90), KetQua NVARCHAR(10), GhiChu NVARCHAR(400));   -- biến bảng KHÔNG bị ROLLBACK xóa
DECLARE @ten NVARCHAR(90), @msg NVARCHAR(400), @chan BIT, @ok BIT, @sl BIGINT, @cb INT;

-- T1 Trigger chan SUA CarbonG
SET @ten = N'T1 Trigger chan SUA CarbonG'; SET @chan = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.KetQuaCarbon(MaSoLieu,NangLuongKWh,CarbonG,HeSoKgKwh,LoaiDuLieu,DoTinCay,NguonHeSo,CongThuc)
        VALUES (@sl, 0.001, 0.5, 0.5, N'UocLuong', N'Thap', N'Nguon test', N'P=nen+k*cpu');
        UPDATE dbo.KetQuaCarbon SET CarbonG = 999 WHERE MaSoLieu = @sl;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
    IF @msg LIKE N'%không được sửa%' OR ERROR_NUMBER() = 3609 SET @chan = 1;   -- 3609 = giao dịch bị trigger ROLLBACK
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @chan = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @chan = 1 THEN N'Bị chặn đúng: ' + @msg ELSE N'Lẽ ra phải bị chặn nhưng đã thực hiện được. ' + @msg END);

-- T2 Cho phep doi co DaKiemTraNguong
SET @ten = N'T2 Cho phep doi co DaKiemTraNguong'; SET @ok = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.KetQuaCarbon(MaSoLieu,NangLuongKWh,CarbonG,HeSoKgKwh,LoaiDuLieu,DoTinCay,NguonHeSo,CongThuc)
        VALUES (@sl, 0.001, 0.5, 0.5, N'UocLuong', N'Thap', N'Nguon test', N'P=nen+k*cpu');
        UPDATE dbo.KetQuaCarbon SET DaKiemTraNguong = 1 WHERE MaSoLieu = @sl;
        IF (SELECT DaKiemTraNguong FROM dbo.KetQuaCarbon WHERE MaSoLieu = @sl) = 1 SET @ok = 1;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @ok = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @ok = 1 THEN N'Đúng như mong đợi' ELSE N'Sai kết quả. ' + @msg END);

-- T3 Trigger chan XOA ket qua carbon
SET @ten = N'T3 Trigger chan XOA ket qua carbon'; SET @chan = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.KetQuaCarbon(MaSoLieu,NangLuongKWh,CarbonG,HeSoKgKwh,LoaiDuLieu,DoTinCay,NguonHeSo,CongThuc)
        VALUES (@sl, 0.001, 0.5, 0.5, N'UocLuong', N'Thap', N'Nguon test', N'P=nen+k*cpu');
        DELETE FROM dbo.KetQuaCarbon WHERE MaSoLieu = @sl;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
    IF @msg LIKE N'%Không được xóa%' OR ERROR_NUMBER() = 3609 SET @chan = 1;   -- 3609 = giao dịch bị trigger ROLLBACK
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @chan = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @chan = 1 THEN N'Bị chặn đúng: ' + @msg ELSE N'Lẽ ra phải bị chặn nhưng đã thực hiện được. ' + @msg END);

-- T4 Them ket qua -> SoLieuHaTang tu thanh DaQuyDoi
SET @ten = N'T4 Them ket qua -> SoLieuHaTang tu thanh DaQuyDoi'; SET @ok = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.KetQuaCarbon(MaSoLieu,NangLuongKWh,CarbonG,HeSoKgKwh,LoaiDuLieu,DoTinCay,NguonHeSo,CongThuc)
        VALUES (@sl, 0.001, 0.5, 0.5, N'UocLuong', N'Thap', N'Nguon test', N'P=nen+k*cpu');
        IF (SELECT TrangThai FROM dbo.SoLieuHaTang WHERE MaSoLieu = @sl) = N'DaQuyDoi' SET @ok = 1;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @ok = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @ok = 1 THEN N'Đúng như mong đợi' ELSE N'Sai kết quả. ' + @msg END);

-- T5 Canh bao DaDong khong mo lai duoc
SET @ten = N'T5 Canh bao DaDong khong mo lai duoc'; SET @chan = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.NguongCanhBao(MaSanPham,ChiTieu,ToanTu,GiaTri) VALUES (N'T_SP', N'Cpu', '>', 80);
        INSERT dbo.CanhBao(MaNguong,MaMoiTruong,GiaTriGanNhat) VALUES (SCOPE_IDENTITY(), N'T_MT', 90);
        SET @cb = SCOPE_IDENTITY();
        UPDATE dbo.CanhBao SET TrangThai = N'DaDong' WHERE MaCanhBao = @cb;
        UPDATE dbo.CanhBao SET TrangThai = N'Mo' WHERE MaCanhBao = @cb;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
    IF @msg LIKE N'%không được mở lại%' OR ERROR_NUMBER() = 3609 SET @chan = 1;   -- 3609 = giao dịch bị trigger ROLLBACK
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @chan = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @chan = 1 THEN N'Bị chặn đúng: ' + @msg ELSE N'Lẽ ra phải bị chặn nhưng đã thực hiện được. ' + @msg END);

-- T6 Doi trang thai canh bao -> ghi NhatKyHeThong
SET @ten = N'T6 Doi trang thai canh bao -> ghi NhatKyHeThong'; SET @ok = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.NguongCanhBao(MaSanPham,ChiTieu,ToanTu,GiaTri) VALUES (N'T_SP', N'Cpu', '>', 80);
        INSERT dbo.CanhBao(MaNguong,MaMoiTruong,GiaTriGanNhat) VALUES (SCOPE_IDENTITY(), N'T_MT', 90);
        SET @cb = SCOPE_IDENTITY();
        UPDATE dbo.CanhBao SET TrangThai = N'DaXacNhan' WHERE MaCanhBao = @cb;
        IF EXISTS (SELECT 1 FROM dbo.NhatKyHeThong WHERE Bang = N'CanhBao' AND MaDoiTuong = CAST(@cb AS NVARCHAR(50)) AND GiaTriCu = N'Mo' AND GiaTriMoi = N'DaXacNhan') SET @ok = 1;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @ok = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @ok = 1 THEN N'Đúng như mong đợi' ELSE N'Sai kết quả. ' + @msg END);

-- T7 Hanh dong DaApDung khong lui trang thai
SET @ten = N'T7 Hanh dong DaApDung khong lui trang thai'; SET @chan = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.HanhDong(MaSanPham,Loai,MoTa,TrangThai) VALUES (N'T_SP', N'Test', N'Mo ta', N'DaApDung');
        UPDATE dbo.HanhDong SET TrangThai = N'DeXuat' WHERE MaSanPham = N'T_SP';
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
    IF @msg LIKE N'%không được quay lại%' OR ERROR_NUMBER() = 3609 SET @chan = 1;   -- 3609 = giao dịch bị trigger ROLLBACK
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @chan = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @chan = 1 THEN N'Bị chặn đúng: ' + @msg ELSE N'Lẽ ra phải bị chặn nhưng đã thực hiện được. ' + @msg END);

-- T8 DELETE SanPham -> chi doi thanh NgungTheoDoi (INSTEAD OF)
SET @ten = N'T8 DELETE SanPham -> chi doi thanh NgungTheoDoi (INSTEAD OF)'; SET @ok = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        DELETE FROM dbo.SanPham WHERE MaSanPham = N'T_SP';
        IF (SELECT TrangThai FROM dbo.SanPham WHERE MaSanPham = N'T_SP') = N'NgungTheoDoi' SET @ok = 1;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @ok = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @ok = 1 THEN N'Đúng như mong đợi' ELSE N'Sai kết quả. ' + @msg END);

-- T9 View thang tra nhan UocLuong
SET @ten = N'T9 View thang tra nhan UocLuong'; SET @ok = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        INSERT dbo.MoiTruong(MaMoiTruong,MaSanPham,TenMoiTruong) VALUES (N'T_MT', N'T_SP', N'May test');
        INSERT dbo.SoLieuHaTang(MaMoiTruong,ThoiDiem,CpuPhanTram,RamMB,OdiaGB,BangThongMB) VALUES (N'T_MT','2026-01-15 10:00',50,1000,100,10);
        SET @sl = SCOPE_IDENTITY();
        INSERT dbo.KetQuaCarbon(MaSoLieu,NangLuongKWh,CarbonG,HeSoKgKwh,LoaiDuLieu,DoTinCay,NguonHeSo,CongThuc)
        VALUES (@sl, 0.001, 0.5, 0.5, N'UocLuong', N'Thap', N'Nguon test', N'P=nen+k*cpu');
        
        IF EXISTS (SELECT 1 FROM dbo.vw_CarbonTheoSanPhamThang WHERE MaSanPham = N'T_SP' AND Nam = 2026 AND Thang = 1 AND NhanTongHop = N'UocLuong' AND SoDiem = 1) SET @ok = 1;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @ok = 1 THEN N'PASS' ELSE N'FAIL' END, CASE WHEN @ok = 1 THEN N'Đúng như mong đợi' ELSE N'Sai kết quả. ' + @msg END);

-- T10 Thủ tục báo lỗi khi sản phẩm không tồn tại
SET @ten = N'T10 usp_TopTrangNang bao loi 50001 khi sai ma san pham'; SET @chan = 0; SET @msg = N'';
BEGIN TRY
    EXEC dbo.usp_TopTrangNang @MaSanPham = N'KHONG_CO';
END TRY
BEGIN CATCH
    SET @msg = ERROR_MESSAGE();
    IF ERROR_NUMBER() = 50001 SET @chan = 1;
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @chan = 1 THEN N'PASS' ELSE N'FAIL' END, @msg);

-- T11 Thủ tục kiểm tra tham số
SET @ten = N'T11 usp_BaoCaoTongHop bao loi 50003 khi SoNgay = 0'; SET @chan = 0; SET @msg = N'';
BEGIN TRY
    BEGIN TRAN;
        INSERT dbo.SanPham(MaSanPham,TenSanPham,KhoaApiBam) VALUES (N'T_SP', N'San pham test', REPLICATE('t',64));
        EXEC dbo.usp_BaoCaoTongHop @MaSanPham = N'T_SP', @SoNgay = 0;
    ROLLBACK;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    SET @msg = ERROR_MESSAGE();
    IF ERROR_NUMBER() = 50003 SET @chan = 1;
END CATCH;
INSERT @kq VALUES (@ten, CASE WHEN @chan = 1 THEN N'PASS' ELSE N'FAIL' END, @msg);

/* ---------- KẾT QUẢ ---------- */
SELECT Test, KetQua, GhiChu FROM @kq ORDER BY Test;
SELECT SUM(CASE WHEN KetQua = N'PASS' THEN 1 ELSE 0 END) AS SoPass, SUM(CASE WHEN KetQua = N'FAIL' THEN 1 ELSE 0 END) AS SoFail FROM @kq;
GO

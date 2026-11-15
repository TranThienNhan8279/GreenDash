# GreenDash – Hướng dẫn SQL để demo cho giảng viên (View · Stored Procedure · Trigger)

Mọi lệnh chạy trong **SSMS** (kết nối `localhost\SQLEXPRESS`), database **GreenDashDB**.
Thứ tự chuẩn bị (làm trước buổi demo):

1. Đã có `01_greendash.sql` + `02_sua_do_chinh_xac.sql` (bạn đã chạy rồi).
2. Mở `03_trigger_view_store.sql` → **F5** (tạo 1 bảng nhật ký, 7 trigger, 1 view, 2 thủ tục). Chạy lại được nhiều lần.
3. Mở `04_demo_kiem_thu.sql` → **F5** → phải thấy bảng **11 dòng PASS**. Đây là bằng chứng "đã kiểm thử".

> Lưu ý trung thực: các script T-SQL được viết và soát tay, chưa chạy thử trên máy mình. Nếu có dòng FAIL hoặc lỗi đỏ, chụp màn hình gửi lại, sẽ sửa ngay. Chạy thử trước buổi demo ít nhất một lần.

---

## 1. Ba khái niệm – nói một câu

| | Là gì | Chạy khi nào | Trong GreenDash |
|---|---|---|---|
| **View** | Câu `SELECT` được đặt tên, như bảng ảo, không lưu dữ liệu | Mỗi lần `SELECT` từ nó | `vw_TongHopCarbonNgay` gộp carbon theo ngày và tự tính nhãn Đo/Ước lượng |
| **Stored procedure** | Khối lệnh T-SQL lưu sẵn, có tham số, gọi bằng `EXEC` | Khi ta gọi | `usp_QuyDoiCarbon` đổi số liệu thành carbon |
| **Trigger** | Khối lệnh tự chạy khi có `INSERT/UPDATE/DELETE` trên một bảng | Tự động, không ai gọi | `TR_KetQuaCarbon_ChanSua` chặn sửa kết quả đã tính |

Câu hỏi hay gặp: *"Khác nhau chỗ nào?"* → View để **đọc**; procedure để **làm một quy trình**, ta chủ động gọi; trigger để **bảo vệ quy tắc nghiệp vụ**, tự chạy kể cả khi ai đó sửa thẳng bằng SQL mà không qua ứng dụng.

---

## 2. Cú pháp tóm tắt (thuộc lòng)

```sql
-- VIEW
CREATE OR ALTER VIEW dbo.vw_Ten AS
SELECT ... FROM ... JOIN ... GROUP BY ...;
GO
SELECT * FROM dbo.vw_Ten WHERE ...;

-- STORED PROCEDURE (có tham số, kiểm tra đầu vào, báo lỗi)
CREATE OR ALTER PROCEDURE dbo.usp_Ten
    @a NVARCHAR(20),
    @b INT = 5                 -- tham số có giá trị mặc định
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.SanPham WHERE MaSanPham = @a)
        THROW 50001, N'Không tìm thấy sản phẩm.', 1;
    SELECT ...;
END;
GO
EXEC dbo.usp_Ten @a = N'SP01', @b = 3;

-- TRIGGER (AFTER)
CREATE OR ALTER TRIGGER dbo.TR_Ten ON dbo.Bang AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted i JOIN deleted d ON d.Ma = i.Ma WHERE <vi phạm>)
    BEGIN
        ROLLBACK TRANSACTION;
        RAISERROR(N'Thông báo lỗi', 16, 1);
    END
END;

-- TRIGGER INSTEAD OF (thay thế hành động gốc)
CREATE OR ALTER TRIGGER dbo.TR_Ten ON dbo.Bang INSTEAD OF DELETE AS
BEGIN
    UPDATE b SET TrangThai = N'Ngung' FROM dbo.Bang b JOIN deleted d ON d.Ma = b.Ma;
END;

-- TRANSACTION + TRY/CATCH
BEGIN TRY
    BEGIN TRAN;
        ... lệnh ...
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    THROW;                      -- ném lại lỗi
END CATCH;
```

Hai bảng đặc biệt trong trigger:

- `inserted` = các dòng **mới** (sau khi INSERT/UPDATE).
- `deleted` = các dòng **cũ** (trước khi UPDATE/DELETE).
- UPDATE có cả hai (`deleted` là giá trị cũ, `inserted` là giá trị mới). INSERT chỉ có `inserted`. DELETE chỉ có `deleted`.

Quy tắc vàng: trigger chạy **một lần cho cả câu lệnh**, câu lệnh có thể đụng nhiều dòng, nên **không** viết `SELECT @x = cột FROM inserted`, mà luôn dùng `JOIN`/`EXISTS` theo tập hợp.

---

## 3. Đối tượng đã có trong dự án

**View (4):** `vw_TongHopCarbonNgay`, `vw_HieuNangTrang`, `vw_CanhBaoDangMo`, và mới `vw_CarbonTheoSanPhamThang`.

**Stored procedure (4):**
- `usp_QuyDoiCarbon` – biến `SoLieuHaTang` thành `KetQuaCarbon` (công thức, hệ số, nhãn).
- `usp_GhiNhanCanhBao` – so sánh với ngưỡng, mở/cập nhật cảnh báo.
- mới `usp_TopTrangNang @MaSanPham, @Top, @SoNgay` – trang nặng nhất.
- mới `usp_BaoCaoTongHop @MaSanPham, @SoNgay` – báo cáo carbon theo ngày.

**Trigger (7), mỗi cái gắn với một quy tắc nghiệp vụ:**

| Trigger | Bảng | Loại | Việc làm |
|---|---|---|---|
| `TR_KetQuaCarbon_ChanSua` | KetQuaCarbon | AFTER UPDATE | Cấm sửa kết quả đã tính (chỉ cho đổi cờ `DaKiemTraNguong`) – để truy vết được |
| `TR_KetQuaCarbon_ChanXoa` | KetQuaCarbon | AFTER DELETE | Cấm xóa kết quả |
| `TR_KetQuaCarbon_DongBoTrangThai` | KetQuaCarbon | AFTER INSERT | Tự đặt số liệu hạ tầng thành `DaQuyDoi` |
| `TR_CanhBao_KhongMoLai` | CanhBao | AFTER UPDATE | Cảnh báo `DaDong` không mở lại được |
| `TR_CanhBao_GhiNhatKy` | CanhBao | AFTER UPDATE | Ghi `NhatKyHeThong` mỗi lần đổi trạng thái (cũ → mới, ai, lúc nào) |
| `TR_HanhDong_KhongLuiTrangThai` | HanhDong | AFTER UPDATE | `DaApDung` không quay về trạng thái trước |
| `TR_SanPham_KhongXoaCung` | SanPham | **INSTEAD OF** DELETE | Xóa sản phẩm chỉ đổi thành `NgungTheoDoi`, giữ lịch sử |

Ràng buộc (CHECK, UNIQUE, FK, filtered unique index `UX_CanhBao_Mo`) cũng là một lớp bảo vệ. Khi bị hỏi *"sao không dùng CHECK mà dùng trigger?"*: CHECK chỉ nhìn **một dòng hiện tại**; điều kiện cần so **giá trị cũ với mới** hoặc nhìn bảng khác thì cần trigger.

---

## 4. Kịch bản demo ~10 phút (copy từng khối vào SSMS)

### Bước 0 – Giới thiệu dữ liệu (1 phút)
```sql
USE GreenDashDB;
SELECT COUNT(*) AS SoDiemHaTang FROM dbo.SoLieuHaTang;
SELECT COUNT(*) AS SoKetQuaCarbon FROM dbo.KetQuaCarbon;
SELECT TOP 5 * FROM dbo.KetQuaCarbon ORDER BY MaKetQua DESC;   -- để ý cột LoaiDuLieu, DoTinCay, CongThuc
```

### Bước 1 – VIEW (2 phút)
```sql
SELECT * FROM dbo.vw_TongHopCarbonNgay ORDER BY Ngay DESC;       -- nhãn tổng hợp Đo/Ước lượng
SELECT * FROM dbo.vw_CarbonTheoSanPhamThang;                      -- view mới: theo tháng
SELECT * FROM dbo.vw_HieuNangTrang;                               -- trang web đã đo
SELECT * FROM dbo.vw_CanhBaoDangMo;
-- Xem định nghĩa view
EXEC sp_helptext N'dbo.vw_TongHopCarbonNgay';
```
Điểm cần nói: view **gộp 3 bảng** (KetQuaCarbon, SoLieuHaTang, MoiTruong), tính **nhãn tổng hợp** (BR12: có dù chỉ 1 điểm ước lượng thì cả ngày là "Ước lượng một phần"), ứng dụng chỉ cần `SELECT`, không lặp lại JOIN.

### Bước 2 – STORED PROCEDURE (3 phút)
```sql
-- Lấy mã sản phẩm có sẵn
SELECT MaSanPham FROM dbo.SanPham;

EXEC dbo.usp_QuyDoiCarbon;                       -- quy đổi các điểm chưa xử lý (nếu không còn điểm mới thì không có dòng nào thêm)
EXEC dbo.usp_GhiNhanCanhBao;

EXEC dbo.usp_BaoCaoTongHop @MaSanPham = N'<MaSanPham của bạn>', @SoNgay = 7;
EXEC dbo.usp_TopTrangNang  @MaSanPham = N'<MaSanPham của bạn>', @Top = 3, @SoNgay = 7;

-- Chứng minh có kiểm tra đầu vào + báo lỗi
EXEC dbo.usp_BaoCaoTongHop @MaSanPham = N'KHONG_CO';             -- lỗi 50001
EXEC dbo.usp_BaoCaoTongHop @MaSanPham = N'<MaSanPham>', @SoNgay = 0; -- lỗi 50003

EXEC sp_helptext N'dbo.usp_QuyDoiCarbon';        -- cho giảng viên xem mã
```
Điểm cần nói về `usp_QuyDoiCarbon`: tính theo **tập hợp** (một câu INSERT…SELECT, không dùng vòng lặp/cursor); công thức `kWh = P × giây / 3600 / 1000`, `gam = kWh × hệ số × 1000`; hệ số lấy theo thứ tự **vùng còn hiệu lực → mặc định quốc gia → không có thì bỏ qua**; có `TRY/CATCH` + `TRANSACTION` nên lỗi giữa chừng thì hoàn tác toàn bộ.

### Bước 3 – TRIGGER: cho giảng viên thấy nó chặn (3 phút)

Mỗi lệnh dưới đây **phải báo lỗi đỏ** – đó là điều ta muốn chứng minh:

```sql
-- (a) Sửa kết quả đã tính → bị chặn
UPDATE dbo.KetQuaCarbon SET CarbonG = 0 WHERE MaKetQua = (SELECT MIN(MaKetQua) FROM dbo.KetQuaCarbon);
-- Msg 50000: Kết quả carbon đã tính không được sửa...  (kèm Msg 3609 "The transaction ended in the trigger")

-- (b) Xóa kết quả → bị chặn
DELETE FROM dbo.KetQuaCarbon WHERE MaKetQua = (SELECT MIN(MaKetQua) FROM dbo.KetQuaCarbon);

-- (c) Dữ liệu vẫn nguyên
SELECT TOP 3 MaKetQua, CarbonG FROM dbo.KetQuaCarbon ORDER BY MaKetQua;
```

Trigger **ghi nhật ký** – cần có ít nhất 1 cảnh báo (nếu chưa có, bỏ qua phần này hoặc dùng bước kiểm thử `04` thay thế):
```sql
SELECT TOP 1 MaCanhBao, TrangThai FROM dbo.CanhBao ORDER BY MaCanhBao;
UPDATE dbo.CanhBao SET TrangThai = N'DaXacNhan' WHERE MaCanhBao = <mã vừa thấy> AND TrangThai = N'Mo';
SELECT * FROM dbo.NhatKyHeThong ORDER BY MaNhatKy DESC;     -- tự có dòng Mo → DaXacNhan
```

INSTEAD OF – **dùng giao dịch để không mất dữ liệu thật**:
```sql
BEGIN TRAN;
    DELETE FROM dbo.SanPham WHERE MaSanPham = N'<MaSanPham của bạn>';
    SELECT MaSanPham, TrangThai FROM dbo.SanPham;     -- vẫn còn, TrangThai = NgungTheoDoi
ROLLBACK;                                              -- hoàn tác, trả lại như cũ
SELECT MaSanPham, TrangThai FROM dbo.SanPham;
```

### Bước 4 – Chạy file kiểm thử (1 phút)
Mở `04_demo_kiem_thu.sql` → F5 → 11 dòng PASS. Nói: *"Mỗi trigger/thủ tục có một test tự động; dữ liệu thử nằm trong giao dịch rồi ROLLBACK nên không ảnh hưởng dữ liệu thật."*

---

## 5. Câu hỏi giảng viên có thể hỏi (trả lời ngắn)

1. **Trigger khác constraint?** CHECK/UNIQUE/FK kiểm tra một dòng hoặc khóa; trigger có thể so sánh cũ/mới (`deleted` vs `inserted`), nhìn bảng khác, ghi nhật ký.
2. **AFTER khác INSTEAD OF?** AFTER chạy sau khi hành động đã xảy ra (có thể ROLLBACK); INSTEAD OF thay hẳn hành động (ta tự quyết làm gì – ở đây đổi xóa thành "ngừng theo dõi").
3. **`inserted` và `deleted` là gì?** Hai bảng ảo của trigger chứa dòng mới và dòng cũ.
4. **Update 100 dòng thì trigger chạy mấy lần?** Một lần, `inserted` có 100 dòng ⇒ phải viết theo tập hợp.
5. **Vì sao có "Msg 3609"?** Trigger đã `ROLLBACK` giao dịch của câu lệnh nên SQL Server báo giao dịch kết thúc trong trigger; đây là hành vi bình thường khi trigger chặn bằng ROLLBACK.
6. **View có lưu dữ liệu không?** Không, chỉ lưu câu SELECT (trừ indexed view). Mỗi lần truy vấn tính lại.
7. **Ưu điểm stored procedure?** Một nơi chứa logic; tham số hóa chống SQL injection; kế hoạch thực thi được lưu; phân quyền chỉ cho `EXEC`; giao dịch trọn gói.
8. **`SET NOCOUNT ON` để làm gì?** Tắt thông báo "n rows affected", giảm lưu lượng và tránh làm client hiểu nhầm.
9. **`THROW` khác `RAISERROR`?** `THROW` mới hơn (2012+), mã lỗi ≥ 50000, có thể ném lại lỗi trong CATCH chỉ bằng `THROW;`. `RAISERROR` cho phép định dạng chuỗi và mức nghiêm trọng.
10. **Vì sao carbon dùng FLOAT khi quy đổi?** Tính trên `DECIMAL` làm cắt phần thập phân (bài học lỗi "0 kg" trước đó); ép `CAST(... AS FLOAT)` rồi mới lưu vào `DECIMAL(18,8)`.
11. **Chống trùng cảnh báo thế nào?** Filtered unique index `UX_CanhBao_Mo (MaNguong, MaMoiTruong) WHERE TrangThai <> 'DaDong'` – mỗi cặp chỉ có một cảnh báo chưa đóng (BR10).
12. **Rủi ro của trigger?** Khó thấy (logic ẩn), có thể làm chậm khi bảng lớn, trigger gọi trigger khác. Cách giảm: ít, ngắn, đặt tên rõ (`TR_Bang_MucDich`), có tài liệu.

---

## 6. Lệnh tiện ích (chạy khi cần)

```sql
-- Liệt kê trigger / view / procedure
SELECT name, OBJECT_NAME(parent_id) AS TrenBang, is_instead_of_trigger, is_disabled FROM sys.triggers WHERE parent_class = 1;
SELECT name FROM sys.views;
SELECT name FROM sys.procedures;

-- Xem mã nguồn
EXEC sp_helptext N'dbo.TR_KetQuaCarbon_ChanSua';

-- Tắt/bật trigger tạm thời (ví dụ khi cần dọn dữ liệu thử lúc phát triển)
DISABLE TRIGGER dbo.TR_KetQuaCarbon_ChanXoa ON dbo.KetQuaCarbon;
DELETE FROM dbo.KetQuaCarbon;               -- chỉ dùng trong môi trường thử
ENABLE  TRIGGER dbo.TR_KetQuaCarbon_ChanXoa ON dbo.KetQuaCarbon;

-- Xóa một đối tượng
DROP TRIGGER IF EXISTS dbo.TR_KetQuaCarbon_ChanXoa;
DROP VIEW IF EXISTS dbo.vw_CarbonTheoSanPhamThang;
DROP PROCEDURE IF EXISTS dbo.usp_TopTrangNang;

-- Xem kế hoạch / thời gian chạy
SET STATISTICS TIME ON;
EXEC dbo.usp_QuyDoiCarbon;
SET STATISTICS TIME OFF;
```

**Cảnh báo quan trọng:** sau khi tạo trigger, lệnh `DELETE FROM dbo.KetQuaCarbon` (hay `TRUNCATE`/script dọn dữ liệu cũ) sẽ bị chặn. Muốn dọn dữ liệu thử thì `DISABLE TRIGGER` trước rồi `ENABLE` lại, và **đừng quên bật lại**. Không dọn trước buổi demo thì không cần động tới.

---

## 7. Bài tập mở rộng (nếu giảng viên yêu cầu làm tại chỗ)

1. Viết view `vw_SanPhamCoCanhBao` liệt kê sản phẩm có cảnh báo đang mở và số lượng.
2. Viết procedure `usp_DongCanhBao @MaCanhBao, @GhiChu` – kiểm tra tồn tại, đổi `DaDong`, ghi `GhiChuDong`, bọc `TRY/CATCH` + `TRAN`.
3. Viết trigger cấm đặt `CongSuatNenW` > 500 trên `MoiTruong` (AFTER INSERT, UPDATE).
4. Dùng `04_demo_kiem_thu.sql` làm mẫu viết thêm một test PASS/FAIL.

Gợi ý bài 3:
```sql
CREATE OR ALTER TRIGGER dbo.TR_MoiTruong_GioiHanCongSuat ON dbo.MoiTruong AFTER INSERT, UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted WHERE CongSuatNenW > 500)
    BEGIN
        ROLLBACK TRANSACTION;
        RAISERROR(N'Công suất nền không được vượt 500 W.', 16, 1);
    END
END;
```

# Siêu Nhân Bán iPhone – Quản lý kho hàng (Django CRUD)

Bài thực hành môn Python. Phát triển tiếp từ bài mẫu `CRUD_Using_Django_Framework`
(project `my_Store_Containers`) của thầy.

Logo nằm ở `static/img/logo.svg` (tự vẽ). Muốn đổi logo: thay file đó, hoặc bỏ ảnh khác
vào `static/img/` rồi sửa đường dẫn trong `templates/base.html`.

## Chạy project

```powershell
cd QuanLyCuaHang_Django
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data        # tạo 3 danh mục + 9 sản phẩm iPhone mẫu (tùy chọn)
python manage.py runserver
```

Mở http://127.0.0.1:8000/store/

- Trang quản trị Django: http://127.0.0.1:8000/admin/ (tạo tài khoản bằng `python manage.py createsuperuser`)
- Chạy test: `python manage.py test inventory`

## Cấu trúc

```
store_config/          cấu hình project (settings, urls)
inventory/             app chính
  models.py            Category, Product
  forms.py             ProductForm, CategoryForm (ModelForm + kiểm tra dữ liệu)
  views.py             class-based views cho CRUD
  urls.py              đường dẫn /store/...
  admin.py             đăng ký model vào trang admin
  templatetags/money.py   filter |vnd  (150000 -> 150.000 ₫)
  management/commands/seed_data.py   lệnh tạo dữ liệu mẫu
  tests.py             13 test
  templates/inventory/ các trang của app
templates/base.html    khung trang dùng chung (thanh bên, tiêu đề, thông báo)
static/css/app.css     giao diện
```

## Khác gì so với bài mẫu

| | Bài mẫu | Bài này |
|---|---|---|
| Dữ liệu | 1 bảng `Product` (tên, giá, mô tả) | Thêm bảng `Category` (khóa ngoại), mã SKU, số lượng tồn, trạng thái kinh doanh, ngày cập nhật |
| View | 3 hàm (`index`, `edit_product`, `delete_product`) | Class-based view: `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView` |
| Kiểm tra dữ liệu | Đọc `request.POST.get()` rồi lưu thẳng | `ModelForm`: tên ≥ 2 ký tự, giá > 0, SKU không trùng (không phân biệt hoa thường) |
| Xóa | Mở link là xóa ngay (GET) | Trang xác nhận, chỉ xóa khi gửi POST |
| Danh sách | Hiện tất cả | Tìm theo tên/SKU, lọc danh mục & tình trạng tồn kho, sắp xếp, phân trang 8 dòng |
| Thống kê | Không có | Giá trị hàng tồn, tổng sản phẩm, sắp hết, hết hàng (dùng `aggregate`) |
| Thông báo | Không có | `messages` framework: "Đã thêm / cập nhật / xóa…" |
| Template | 1 file `index.html` | `base.html` + kế thừa `{% extends %}`, `{% include %}` cho ô nhập |
| Giá tiền | `150000đ` | Filter tự viết: `150.000 ₫` |
| Cài đặt | `en-us`, `UTC` | Tiếng Việt, giờ Việt Nam; khóa bí mật đọc từ biến môi trường |
| Test | Không có | 13 test (model, form, view) |

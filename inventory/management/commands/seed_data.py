from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from inventory.models import Category, Product

SAMPLE = {
    "iPhone mới": [
        ("IP17PM-256", "iPhone 17 Pro Max 256GB", 34990000, 12, "Màn hình 6.9 inch, chip A19 Pro, khung titan."),
        ("IP17P-256", "iPhone 17 Pro 256GB", 30990000, 4, "Màn hình 6.3 inch, chip A19 Pro."),
        ("IP17-128", "iPhone 17 128GB", 22990000, 20, "Bản tiêu chuẩn, màn hình 6.3 inch."),
        ("IPAIR-256", "iPhone Air 256GB", 28990000, 0, "Thân máy siêu mỏng."),
    ],
    "iPhone cũ": [
        ("IP16PM-256-LN", "iPhone 16 Pro Max 256GB (like new)", 25490000, 3, "Pin 96%, bảo hành 6 tháng."),
        ("IP15-128-LN", "iPhone 15 128GB (like new)", 13990000, 7, "Pin 91%, máy đẹp 99%."),
    ],
    "Phụ kiện": [
        ("APP3", "AirPods Pro 3", 6490000, 15, "Chống ồn chủ động, hộp sạc USB-C."),
        ("MAGSAFE-25W", "Sạc MagSafe 25W", 1190000, 0, "Sạc không dây cho iPhone 12 trở lên."),
        ("CASE-17PM", "Ốp lưng silicone iPhone 17 Pro Max", 1390000, 5, "Hỗ trợ MagSafe."),
    ],
}

# Tai khoan mau de thay/ban dang nhap thu. Chi dung de demo - dung that thi doi mat khau.
DEMO_USERNAME = "quanly"
DEMO_PASSWORD = "quanly123"

# Ma SKU cua bo du lieu mau cu (quan ao / do dien tu / van phong pham).
OLD_SAMPLE_SKUS = ["AO-001", "AO-002", "QU-001", "DT-001", "DT-002", "DT-003", "VP-001", "VP-002", "VP-003"]
OLD_SAMPLE_CATEGORIES = ["Thời trang", "Đồ điện tử", "Văn phòng phẩm"]


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cửa hàng iPhone (3 danh mục, 9 sản phẩm). Chạy lại nhiều lần không bị trùng."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace-old",
            action="store_true",
            help="Xóa bộ dữ liệu mẫu cũ (quần áo, đồ điện tử, văn phòng phẩm) trước khi thêm.",
        )

    def handle(self, *args, **options):
        if options["replace_old"]:
            Product.objects.filter(sku__in=OLD_SAMPLE_SKUS).delete()
            Category.objects.filter(name__in=OLD_SAMPLE_CATEGORIES, products__isnull=True).delete()

        created = 0
        for category_name, items in SAMPLE.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for sku, name, price, quantity, description in items:
                _, is_new = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "name": name,
                        "price": price,
                        "quantity": quantity,
                        "category": category,
                        "description": description,
                    },
                )
                created += is_new
        User = get_user_model()
        if not User.objects.filter(username=DEMO_USERNAME).exists():
            # is_staff: vao duoc ca trang /admin/ cua Django.
            User.objects.create_user(DEMO_USERNAME, password=DEMO_PASSWORD, is_staff=True, is_superuser=True)
            self.stdout.write(f"Da tao tai khoan mau: {DEMO_USERNAME} / {DEMO_PASSWORD}")

        # Khong dau: cua so lenh Windows mac dinh (cp1252) in tieng Viet co dau se bao loi.
        self.stdout.write(self.style.SUCCESS(f"Da them {created} san pham mau."))

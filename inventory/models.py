from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Danh muc san pham (ban goc chua co - moi san pham nam chung mot cho)."""

    name = models.CharField("Tên danh mục", max_length=100, unique=True)
    description = models.CharField("Mô tả", max_length=255, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("inventory:category_detail", args=[self.pk])


class Product(models.Model):
    class Status(models.TextChoices):
        IN_STOCK = "in_stock", "Còn hàng"
        LOW_STOCK = "low_stock", "Sắp hết"
        OUT_OF_STOCK = "out_of_stock", "Hết hàng"

    name = models.CharField("Tên sản phẩm", max_length=255)
    sku = models.CharField(
        "Mã SKU", max_length=30, unique=True, help_text="Mã riêng của từng sản phẩm, vd: IP17P-256"
    )
    # Xoa danh muc thi san pham van con, chi mat danh muc (SET_NULL).
    category = models.ForeignKey(
        Category,
        verbose_name="Danh mục",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    price = models.DecimalField(
        "Giá bán", max_digits=12, decimal_places=0, validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField("Số lượng tồn", default=0)
    description = models.TextField("Mô tả", blank=True)
    is_active = models.BooleanField("Đang kinh doanh", default=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def get_absolute_url(self):
        return reverse("inventory:product_detail", args=[self.pk])

    @property
    def stock_status(self):
        if self.quantity == 0:
            return self.Status.OUT_OF_STOCK
        if self.quantity <= settings.LOW_STOCK_THRESHOLD:
            return self.Status.LOW_STOCK
        return self.Status.IN_STOCK

    @property
    def stock_label(self):
        return self.Status(self.stock_status).label

    @property
    def stock_value(self):
        """Gia tri hang ton = gia x so luong."""
        return self.price * self.quantity

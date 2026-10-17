from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Category, Product


def normalize(text):
    """Gop khoang trang thua: "  iPhone   moi " -> "iPhone moi"."""
    return " ".join(text.split())


def same_name(a, b):
    # casefold() so sanh khong phan biet hoa thuong, ke ca chu co dau ("Mới" == "MỚI").
    # Khong dung name__iexact vi SQLite chi bo qua hoa thuong voi chu khong dau.
    return normalize(a).casefold() == normalize(b).casefold()


class StyledFormMixin:
    """Gan class CSS cho moi o nhap, de template khong phai viet tay tung o."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "check" if isinstance(field.widget, forms.CheckboxInput) else "input"
            field.widget.attrs.setdefault("class", css)


class LoginForm(StyledFormMixin, AuthenticationForm):
    """Form dang nhap co san cua Django, chi them class CSS cho o nhap."""


class ProductForm(StyledFormMixin, forms.ModelForm):
    """
    Ban goc doc tung o bang request.POST.get() roi luu thang, nen nhap gia am
    hay bo trong ten van luu duoc. ModelForm kiem tra du lieu truoc khi luu.
    """

    class Meta:
        model = Product
        fields = ["name", "sku", "category", "price", "quantity", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Vd: iPhone 17 Pro 256GB"}),
            "sku": forms.TextInput(attrs={"placeholder": "Vd: IP17P-256"}),
            "price": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "Vd: 150000"}),
            "quantity": forms.NumberInput(attrs={"min": 0}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Màn hình, chip, dung lượng, màu sắc..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "— Chưa phân loại —"

    def clean_name(self):
        name = normalize(self.cleaned_data["name"])
        if len(name) < 2:
            raise forms.ValidationError("Tên sản phẩm phải có ít nhất 2 ký tự.")
        return name

    def clean_sku(self):
        # Luu SKU chu hoa de "ip17-128" va "IP17-128" khong thanh 2 san pham.
        sku = self.cleaned_data["sku"].strip().upper()
        if " " in sku:
            raise forms.ValidationError("Mã SKU không được chứa khoảng trắng.")
        exists = Product.objects.filter(sku=sku).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError("Mã SKU này đã có sản phẩm khác dùng.")
        return sku

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Giá bán phải lớn hơn 0.")
        return price

    def clean(self):
        # Trong cung mot danh muc khong duoc co 2 san pham trung ten.
        # Khac danh muc thi duoc (vd: "iPhone 15" o ca "iPhone moi" va "iPhone cu").
        cleaned = super().clean()
        name, category = cleaned.get("name"), cleaned.get("category")
        if name:
            others = Product.objects.filter(category=category).exclude(pk=self.instance.pk)
            if any(same_name(name, other) for other in others.values_list("name", flat=True)):
                where = f"danh mục “{category}”" if category else "nhóm “Chưa phân loại”"
                self.add_error("name", f"Đã có sản phẩm tên “{name}” trong {where}.")
        return cleaned


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Vd: Phụ kiện"}),
            "description": forms.TextInput(attrs={"placeholder": "Mô tả ngắn (không bắt buộc)"}),
        }

    def clean_name(self):
        name = normalize(self.cleaned_data["name"])
        others = Category.objects.exclude(pk=self.instance.pk).values_list("name", flat=True)
        if any(same_name(name, other) for other in others):
            raise forms.ValidationError(f"Danh mục “{name}” đã có rồi.")
        return name

"""
View dang lop (class-based view) thay cho 3 ham index / edit_product / delete_product
cua ban goc. Moi thao tac CRUD tach thanh mot trang rieng:

    Danh sach   ProductListView    GET  /store/
    Chi tiet    ProductDetailView  GET  /store/<pk>/
    Them        ProductCreateView  GET/POST /store/them/
    Sua         ProductUpdateView  GET/POST /store/<pk>/sua/
    Xoa         ProductDeleteView  GET (hoi lai) / POST (xoa that) /store/<pk>/xoa/

Danh muc cung du CRUD tuong tu duoi /store/danh-muc/, trang chi tiet liet ke san pham.
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Prefetch, Q, Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CategoryForm, ProductForm
from .models import Category, Product

# Chi cho phep sap xep theo cac cot nay - khong dua thang gia tri tu URL vao order_by().
SORT_OPTIONS = {
    "newest": ("-created_at", "Mới nhất"),
    "name": ("name", "Tên A → Z"),
    "price_asc": ("price", "Giá tăng dần"),
    "price_desc": ("-price", "Giá giảm dần"),
    "stock": ("quantity", "Tồn kho ít nhất"),
}


# ---------------------------------------------------------------- San pham

class ProductListView(ListView):
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 8

    def get_queryset(self):
        # select_related: lay danh muc cung luc, tranh moi dong lai hoi CSDL mot lan.
        qs = Product.objects.select_related("category")
        params = self.request.GET

        keyword = params.get("q", "").strip()
        if keyword:
            qs = qs.filter(Q(name__icontains=keyword) | Q(sku__icontains=keyword))

        category = params.get("category", "")
        if category == "none":
            qs = qs.filter(category__isnull=True)
        elif category.isdigit():
            qs = qs.filter(category_id=category)

        low = settings.LOW_STOCK_THRESHOLD
        status = params.get("status", "")
        if status == Product.Status.OUT_OF_STOCK:
            qs = qs.filter(quantity=0)
        elif status == Product.Status.LOW_STOCK:
            qs = qs.filter(quantity__gt=0, quantity__lte=low)
        elif status == Product.Status.IN_STOCK:
            qs = qs.filter(quantity__gt=low)

        sort = params.get("sort", "newest")
        order = SORT_OPTIONS.get(sort, SORT_OPTIONS["newest"])[0]
        return qs.order_by(order, "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = Product.objects.all()
        value_expr = ExpressionWrapper(
            F("price") * F("quantity"), output_field=DecimalField(max_digits=20, decimal_places=0)
        )
        low = settings.LOW_STOCK_THRESHOLD
        stats = all_products.aggregate(
            total=Count("id"),
            units=Sum("quantity"),
            value=Sum(value_expr),
            in_stock=Count("id", filter=Q(quantity__gt=low)),
            low_stock=Count("id", filter=Q(quantity__gt=0, quantity__lte=low)),
            out_of_stock=Count("id", filter=Q(quantity=0)),
        )
        # "Suc khoe kho" = ti le san pham con hang du (the toi mau dau trang).
        stats["health"] = round(stats["in_stock"] * 100 / stats["total"]) if stats["total"] else 0
        context["stats"] = stats

        # Tab trang thai kem so dem, moi tab giu nguyen tu khoa tim kiem / danh muc dang chon.
        tab_query = self.request.GET.copy()
        for key in ("status", "page"):
            tab_query.pop(key, None)
        base = tab_query.urlencode()
        counts = {
            "": stats["total"],
            Product.Status.IN_STOCK: stats["in_stock"],
            Product.Status.LOW_STOCK: stats["low_stock"],
            Product.Status.OUT_OF_STOCK: stats["out_of_stock"],
        }
        tabs = [("", "Tất cả")] + list(Product.Status.choices)
        context["status_tabs"] = [
            {
                "label": label,
                "count": counts[value],
                "active": self.request.GET.get("status", "") == value,
                "query": "&".join(p for p in (base, f"status={value}" if value else "") if p),
            }
            for value, label in tabs
        ]

        # Giu lai bo loc khi bam sang trang 2, 3... (bo tham so page cu).
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            categories=Category.objects.all(),
            statuses=Product.Status.choices,
            sort_options=[(key, label) for key, (_, label) in SORT_OPTIONS.items()],
            current=self.request.GET,
            querystring=query.urlencode(),
            is_filtered=any(self.request.GET.get(k) for k in ("q", "category", "status")),
        )
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "inventory/product_detail.html"
    context_object_name = "product"


class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Đã thêm sản phẩm “%(name)s”."

    def get_initial(self):
        # Bam "Them san pham" tu trang danh muc thi chon san danh muc do.
        initial = super().get_initial()
        category = self.request.GET.get("category")
        if category and category.isdigit():
            initial["category"] = category
        return initial


class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_message = "Đã cập nhật sản phẩm “%(name)s”."

    def get_success_url(self):
        return self.object.get_absolute_url()


class ProductDeleteView(DeleteView):
    """
    Ban goc xoa ngay khi mo link (GET) - trinh duyet tai truoc link hay bam nham
    la mat du lieu. O day GET chi hien trang hoi lai, POST moi xoa that.
    """

    model = Product
    template_name = "inventory/confirm_delete.html"
    success_url = reverse_lazy("inventory:product_list")

    def form_valid(self, form):
        messages.success(self.request, f"Đã xóa sản phẩm “{self.object.name}”.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(kind="sản phẩm", cancel_url=self.object.get_absolute_url())
        return context


# ---------------------------------------------------------------- Danh muc

class CategoryListView(ListView):
    template_name = "inventory/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # prefetch_related: lay san pham cua moi danh muc trong 1 lan hoi, de hien ten ngay tren bang.
        return (
            Category.objects.annotate(product_count=Count("products"))
            .prefetch_related(Prefetch("products", queryset=Product.objects.order_by("name")))
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Form them nhanh nam ngay tren trang danh sach.
        context.setdefault("form", CategoryForm())
        return context


class CategoryDetailView(DetailView):
    """Xem mot danh muc va toan bo san pham dang nam trong do."""

    model = Category
    template_name = "inventory/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.object.products.order_by("name")
        value_expr = ExpressionWrapper(
            F("price") * F("quantity"), output_field=DecimalField(max_digits=20, decimal_places=0)
        )
        context.update(
            products=products,
            stats=products.aggregate(total=Count("id"), units=Sum("quantity"), value=Sum(value_expr)),
        )
        return context


class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Đã thêm danh mục “%(name)s”."


class CategoryUpdateView(SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Đã đổi danh mục thành “%(name)s”."


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = "inventory/confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Đã xóa danh mục “{self.object.name}”. Các sản phẩm trong đó chuyển sang “Chưa phân loại”.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            kind="danh mục",
            cancel_url=reverse_lazy("inventory:category_list"),
            note=f"{self.object.products.count()} sản phẩm trong danh mục này sẽ không bị xóa, "
            "chỉ chuyển sang “Chưa phân loại”.",
        )
        return context

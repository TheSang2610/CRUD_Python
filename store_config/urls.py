from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("store/", include("inventory.urls")),
    # Vao trang goc thi chuyen thang toi danh sach san pham.
    path("", RedirectView.as_view(pattern_name="inventory:product_list", permanent=False)),
]

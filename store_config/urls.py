from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path
from django.views.generic import RedirectView

from inventory.forms import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("store/", include("inventory.urls")),
    # Trang dang nhap / dang xuat co san cua Django (template: templates/registration/login.html).
    path("tai-khoan/login/", LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("tai-khoan/", include("django.contrib.auth.urls")),
    # Vao trang goc thi chuyen thang toi danh sach san pham.
    path("", RedirectView.as_view(pattern_name="inventory:product_list", permanent=False)),
]

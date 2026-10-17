from django.urls import path

from . import views

# app_name: goi ten url theo dang "inventory:product_list", khong dung ten trung voi app khac.
app_name = "inventory"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("them/", views.ProductCreateView.as_view(), name="product_create"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("<int:pk>/sua/", views.ProductUpdateView.as_view(), name="product_update"),
    path("<int:pk>/xoa/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("danh-muc/", views.CategoryListView.as_view(), name="category_list"),
    path("danh-muc/them/", views.CategoryCreateView.as_view(), name="category_create"),
    path("danh-muc/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("danh-muc/<int:pk>/sua/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("danh-muc/<int:pk>/xoa/", views.CategoryDeleteView.as_view(), name="category_delete"),
]

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "price", "quantity", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku")
    list_editable = ("price", "quantity", "is_active")

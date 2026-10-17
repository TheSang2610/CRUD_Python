from django.test import TestCase
from django.urls import reverse

from .forms import CategoryForm, ProductForm
from .models import Category, Product


class ProductModelTests(TestCase):
    def test_stock_status_by_quantity(self):
        self.assertEqual(Product(quantity=0).stock_status, Product.Status.OUT_OF_STOCK)
        self.assertEqual(Product(quantity=3).stock_status, Product.Status.LOW_STOCK)
        self.assertEqual(Product(quantity=20).stock_status, Product.Status.IN_STOCK)

    def test_stock_value(self):
        self.assertEqual(Product(price=150000, quantity=4).stock_value, 600000)


class ProductFormTests(TestCase):
    def data(self, **overrides):
        base = {"name": "Áo thun", "sku": "ao-01", "price": 150000, "quantity": 5, "is_active": True}
        base.update(overrides)
        return base

    def test_sku_is_uppercased(self):
        form = ProductForm(data=self.data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["sku"], "AO-01")

    def test_rejects_zero_or_negative_price(self):
        self.assertFalse(ProductForm(data=self.data(price=0)).is_valid())
        self.assertFalse(ProductForm(data=self.data(price=-5)).is_valid())

    def test_rejects_duplicate_sku_ignoring_case(self):
        Product.objects.create(name="Cũ", sku="AO-01", price=1000)
        form = ProductForm(data=self.data(sku="ao-01"))
        self.assertFalse(form.is_valid())
        self.assertIn("sku", form.errors)


class ProductViewTests(TestCase):
    def setUp(self):
        self.fashion = Category.objects.create(name="Thời trang")
        self.shirt = Product.objects.create(
            name="Áo sơ mi", sku="AO-002", price=300000, quantity=0, category=self.fashion
        )
        self.mouse = Product.objects.create(name="Chuột", sku="DT-003", price=199000, quantity=25)

    def test_list_search_by_name_or_sku(self):
        res = self.client.get(reverse("inventory:product_list"), {"q": "dt-003"})
        self.assertContains(res, "Chuột")
        self.assertNotContains(res, "Áo sơ mi")

    def test_list_filter_out_of_stock(self):
        res = self.client.get(reverse("inventory:product_list"), {"status": "out_of_stock"})
        self.assertEqual(list(res.context["products"]), [self.shirt])

    def test_unknown_sort_falls_back_to_newest(self):
        res = self.client.get(reverse("inventory:product_list"), {"sort": "id; DROP TABLE"})
        self.assertEqual(res.status_code, 200)

    def test_create_product(self):
        res = self.client.post(
            reverse("inventory:product_create"),
            {"name": "Sổ tay", "sku": "vp-9", "price": 50000, "quantity": 10, "is_active": "on"},
        )
        self.assertRedirects(res, reverse("inventory:product_list"))
        self.assertTrue(Product.objects.filter(sku="VP-9").exists())

    def test_invalid_create_shows_errors_and_saves_nothing(self):
        res = self.client.post(reverse("inventory:product_create"), {"name": "", "sku": "", "price": -1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Product.objects.count(), 2)

    def test_update_product(self):
        self.client.post(
            reverse("inventory:product_update", args=[self.mouse.pk]),
            {"name": "Chuột gaming", "sku": "DT-003", "price": 250000, "quantity": 7},
        )
        self.mouse.refresh_from_db()
        self.assertEqual(self.mouse.name, "Chuột gaming")
        self.assertEqual(self.mouse.quantity, 7)

    def test_delete_needs_post(self):
        url = reverse("inventory:product_delete", args=[self.mouse.pk])
        self.client.get(url)  # chi mo trang hoi lai
        self.assertTrue(Product.objects.filter(pk=self.mouse.pk).exists())
        self.client.post(url)
        self.assertFalse(Product.objects.filter(pk=self.mouse.pk).exists())

    def test_deleting_category_keeps_products(self):
        self.client.post(reverse("inventory:category_delete", args=[self.fashion.pk]))
        self.shirt.refresh_from_db()
        self.assertIsNone(self.shirt.category)


class DuplicateTests(TestCase):
    def setUp(self):
        self.new = Category.objects.create(name="iPhone mới")
        self.used = Category.objects.create(name="iPhone cũ")
        self.p = Product.objects.create(name="iPhone 15 128GB", sku="IP15", price=1000, category=self.new)

    def product_data(self, **overrides):
        base = {"name": "iPhone 15 128GB", "sku": "IP15-B", "price": 1000, "quantity": 1, "category": self.new.pk}
        base.update(overrides)
        return base

    def test_category_name_duplicate_ignores_case_accents_and_spaces(self):
        for name in ["iPhone mới", "IPHONE MỚI", "  iphone   mới "]:
            form = CategoryForm(data={"name": name})
            self.assertFalse(form.is_valid(), name)
            self.assertIn("name", form.errors)

    def test_category_can_be_saved_with_its_own_name(self):
        form = CategoryForm(data={"name": "IPHONE MỚI"}, instance=self.new)
        self.assertTrue(form.is_valid(), form.errors)

    def test_product_name_duplicate_in_same_category(self):
        form = ProductForm(data=self.product_data(name="IPHONE 15  128gb"))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_product_name_allowed_in_other_category(self):
        form = ProductForm(data=self.product_data(category=self.used.pk))
        self.assertTrue(form.is_valid(), form.errors)

    def test_product_duplicate_without_category(self):
        Product.objects.create(name="Cáp sạc", sku="CAP-1", price=1000)
        form = ProductForm(data=self.product_data(name="cáp sạc", category=""))
        self.assertFalse(form.is_valid())

    def test_editing_product_keeps_own_name(self):
        form = ProductForm(data=self.product_data(sku="IP15", quantity=9), instance=self.p)
        self.assertTrue(form.is_valid(), form.errors)

    def test_moving_product_into_category_with_same_name_is_blocked(self):
        other = Product.objects.create(name="iPhone 15 128GB", sku="IP15-U", price=900, category=self.used)
        form = ProductForm(data=self.product_data(sku="IP15-U"), instance=other)
        self.assertFalse(form.is_valid())

    def test_duplicate_category_via_view_saves_nothing(self):
        res = self.client.post(reverse("inventory:category_create"), {"name": "iphone MỚI"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Category.objects.count(), 2)


class CategoryDetailTests(TestCase):
    def test_detail_lists_only_its_products(self):
        a = Category.objects.create(name="Phụ kiện")
        b = Category.objects.create(name="iPhone cũ")
        Product.objects.create(name="Sạc MagSafe", sku="MS", price=1000, quantity=2, category=a)
        Product.objects.create(name="iPhone 13", sku="IP13", price=5000, quantity=1, category=b)
        res = self.client.get(reverse("inventory:category_detail", args=[a.pk]))
        self.assertContains(res, "Sạc MagSafe")
        self.assertNotContains(res, "iPhone 13")
        self.assertEqual(res.context["stats"]["total"], 1)

    def test_list_shows_product_names(self):
        a = Category.objects.create(name="Phụ kiện")
        Product.objects.create(name="AirPods Pro 3", sku="APP3", price=1000, category=a)
        res = self.client.get(reverse("inventory:category_list"))
        self.assertContains(res, "AirPods Pro 3")

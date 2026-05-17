from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.signals import user_logged_in
from decimal import Decimal

from accounts.models import Role, User
from admin_panel.models import ActivityLog
from admin_panel.signals import log_user_login
from menu.models import Category, Dish, DishIngredient
from orders.models import Order, OrderItem
from stock.models import Ingredient, IngredientCategory
from tables.models import RestaurantTable, TableStatus, TableZone


class TableRepositionViewTests(TestCase):
    def setUp(self):
        user_logged_in.disconnect(log_user_login)
        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            role=Role.ADMIN,
        )
        self.table = RestaurantTable.objects.create(
            name="T1",
            number=1,
            zone=TableZone.INTERIEUR,
            capacity=4,
            status=TableStatus.AVAILABLE,
            pos_x=50,
            pos_y=50,
        )

    def tearDown(self):
        user_logged_in.connect(log_user_login)

    def test_admin_can_reposition_table(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:table_reposition", args=[self.table.id]),
            {"pos_x": "12.4", "pos_y": "88.6"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"success": True, "pos_x": 12, "pos_y": 89, "zone": "terrasse", "zone_label": "Terrasse"},
        )

        self.table.refresh_from_db()
        self.assertEqual(self.table.pos_x, 12)
        self.assertEqual(self.table.pos_y, 89)
        self.assertEqual(self.table.zone, TableZone.TERRASSE)



class DishDeleteViewTests(TestCase):
    def setUp(self):
        user_logged_in.disconnect(log_user_login)
        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            role=Role.ADMIN,
        )
        self.category = Category.objects.create(
            name="Plats",
            slug="plats",
        )

    def tearDown(self):
        user_logged_in.connect(log_user_login)

    def test_unused_dish_is_deleted(self):
        dish = Dish.objects.create(
            category=self.category,
            name="Pizza",
            slug="pizza",
            price="120.00",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:dish_delete", args=[dish.id]),
        )

        self.assertRedirects(response, reverse("admin_panel:menu_admin"))
        self.assertFalse(Dish.objects.filter(id=dish.id).exists())
        self.assertTrue(
            ActivityLog.objects.filter(
                module="Menu",
                object_id=str(dish.id),
                description__icontains="supprime",
            ).exists()
        )

    def test_dish_linked_to_order_is_deactivated(self):
        dish = Dish.objects.create(
            category=self.category,
            name="Burger",
            slug="burger",
            price="80.00",
        )
        order = Order.objects.create(
            customer_name="Client Test",
            mode=Order.TAKEAWAY,
            status=Order.PENDING,
        )
        OrderItem.objects.create(
            order=order,
            dish=dish,
            dish_name=dish.name,
            quantity=1,
            unit_price="80.00",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:dish_delete", args=[dish.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse("admin_panel:menu_admin"))

        dish.refresh_from_db()
        self.assertFalse(dish.is_active)
        self.assertFalse(dish.manual_available)
        self.assertTrue(Dish.objects.filter(id=dish.id).exists())
        self.assertTrue(
            ActivityLog.objects.filter(
                module="Menu",
                object_id=str(dish.id),
                description__icontains="desactive",
            ).exists()
        )

    def test_dish_linked_only_to_completed_order_is_deleted(self):
        dish = Dish.objects.create(
            category=self.category,
            name="Tacos",
            slug="tacos",
            price="65.00",
        )
        order = Order.objects.create(
            customer_name="Client Archive",
            mode=Order.TAKEAWAY,
            status=Order.DELIVERED,
        )
        item = OrderItem.objects.create(
            order=order,
            dish=dish,
            dish_name=dish.name,
            quantity=2,
            unit_price="65.00",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:dish_delete", args=[dish.id]),
        )

        self.assertRedirects(response, reverse("admin_panel:menu_admin"))
        self.assertFalse(Dish.objects.filter(id=dish.id).exists())

        item.refresh_from_db()
        self.assertIsNone(item.dish)
        self.assertEqual(item.display_name, "Tacos")


class StockCategoryCrudTests(TestCase):
    def setUp(self):
        user_logged_in.disconnect(log_user_login)
        self.admin = User.objects.create_user(
            username="stockadmin",
            password="testpass123",
            role=Role.ADMIN,
        )

    def tearDown(self):
        user_logged_in.connect(log_user_login)

    def test_can_create_stock_category(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:ingredient_category_create"),
            {
                "name": "Épices",
                "slug": "epices",
                "ordering": 1,
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("admin_panel:stock"))
        self.assertTrue(IngredientCategory.objects.filter(slug="epices").exists())

    def test_stock_category_with_ingredients_is_deactivated(self):
        category = IngredientCategory.objects.create(
            name="Légumes",
            slug="legumes",
        )
        Ingredient.objects.create(
            category=category,
            name="Tomate",
            quantity="10.00",
            unit="kg",
            unit_price="2.00",
            alert_threshold="3.00",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:ingredient_category_delete", args=[category.id]),
        )

        self.assertRedirects(response, reverse("admin_panel:stock"))
        category.refresh_from_db()
        self.assertFalse(category.is_active)


class StockFilterTests(TestCase):
    def setUp(self):
        user_logged_in.disconnect(log_user_login)
        self.admin = User.objects.create_user(
            username="filteradmin",
            password="testpass123",
            role=Role.ADMIN,
        )
        self.spices = IngredientCategory.objects.create(name="Épices", slug="epices")
        self.dairy = IngredientCategory.objects.create(name="Laitages", slug="laitages")
        Ingredient.objects.create(
            category=self.spices,
            name="Poivre",
            quantity="5.00",
            unit="g",
            unit_price="1.00",
            alert_threshold="1.00",
        )
        Ingredient.objects.create(
            category=self.dairy,
            name="Beurre",
            quantity="3.00",
            unit="kg",
            unit_price="4.00",
            alert_threshold="1.00",
        )

    def tearDown(self):
        user_logged_in.connect(log_user_login)

    def test_stock_page_filters_by_category(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("admin_panel:stock"),
            {"category": str(self.spices.id)},
        )

        self.assertContains(response, "Poivre")
        self.assertNotContains(response, "Beurre")


class MenuFilterTests(TestCase):
    def setUp(self):
        user_logged_in.disconnect(log_user_login)
        self.admin = User.objects.create_user(
            username="menuadmin",
            password="testpass123",
            role=Role.ADMIN,
        )
        self.pizza_category = Category.objects.create(name="Pizzas", slug="pizzas")
        self.drink_category = Category.objects.create(name="Boissons", slug="boissons")
        Dish.objects.create(
            category=self.pizza_category,
            name="Margherita",
            slug="margherita",
            price="90.00",
        )
        Dish.objects.create(
            category=self.drink_category,
            name="Citronnade",
            slug="citronnade",
            price="20.00",
        )

    def tearDown(self):
        user_logged_in.connect(log_user_login)

    def test_menu_page_filters_by_category_and_search(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("admin_panel:menu_admin"),
            {"category": str(self.pizza_category.id), "q": "marg"},
        )

        self.assertContains(response, "Margherita")
        self.assertNotContains(response, "Citronnade")


class DishIngredientCostTests(TestCase):
    def test_cost_uses_price_per_1000g_for_gram_stock(self):
        category = Category.objects.create(name="Tests", slug="tests")
        dish = Dish.objects.create(
            category=category,
            name="Sauce",
            slug="sauce",
            price="50.00",
        )
        ingredient = Ingredient.objects.create(
            name="Farine",
            quantity="5000.00",
            unit="g",
            unit_price="20.00",
            alert_threshold="100.00",
        )
        composition = DishIngredient.objects.create(
            dish=dish,
            ingredient=ingredient,
            quantity="250.00",
            unit="g",
        )

        self.assertEqual(composition.cost, Decimal("5.00"))

    def test_cost_uses_price_per_kg_for_kilo_stock(self):
        category = Category.objects.create(name="Tests 2", slug="tests-2")
        dish = Dish.objects.create(
            category=category,
            name="Pâte",
            slug="pate",
            price="50.00",
        )
        ingredient = Ingredient.objects.create(
            name="Semoule",
            quantity="20.00",
            unit="kg",
            unit_price="20.00",
            alert_threshold="2.00",
        )
        composition = DishIngredient.objects.create(
            dish=dish,
            ingredient=ingredient,
            quantity="500.00",
            unit="g",
        )

        self.assertEqual(composition.cost, Decimal("10.00"))


class TableSortingTests(TestCase):
    def setUp(self):
        user_logged_in.disconnect(log_user_login)
        self.admin = User.objects.create_user(
            username="tableadmin",
            password="testpass123",
            role=Role.ADMIN,
        )
        RestaurantTable.objects.create(
            name="B Table",
            number=2,
            zone=TableZone.VIP,
            capacity=4,
            status=TableStatus.OCCUPIED,
            pos_x=80,
            pos_y=20,
        )
        RestaurantTable.objects.create(
            name="A Table",
            number=1,
            zone=TableZone.TERRASSE,
            capacity=2,
            status=TableStatus.AVAILABLE,
            pos_x=20,
            pos_y=80,
        )

    def tearDown(self):
        user_logged_in.connect(log_user_login)

    def test_tables_page_sorts_by_name_ascending(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("admin_panel:tables"),
            {"sort": "name", "dir": "asc"},
        )

        tables = list(response.context["tables"])
        self.assertEqual([table.name for table in tables], ["A Table", "B Table"])

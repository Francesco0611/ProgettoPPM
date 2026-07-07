from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Category, Product, CartItem, Order

User = get_user_model()

class StoreApiTests(APITestCase):
    def setUp(self):
        # Create users with different roles
        self.customer = User.objects.create_user(
            username='customer_user', password='password123', role='customer'
        )
        self.manager = User.objects.create_user(
            username='manager_user', password='password123', role='manager'
        )
        
        # Create initial Category and Product
        self.category = Category.objects.create(name='Electronics', description='Gadgets')
        self.product = Product.objects.create(
            category=self.category,
            name='Smartphone X',
            price=499.99,
            stock=5,
            is_active=True
        )

        # Endpoints
        self.category_list_url = reverse('category-list')
        self.category_detail_url = reverse('category-detail', args=[self.category.id])
        self.product_list_url = reverse('product-list')
        self.product_detail_url = reverse('product-detail', args=[self.product.id])
        self.cart_list_url = reverse('cart-list')
        self.order_list_url = reverse('order-list')

    def test_public_can_list_products_and_categories(self):
        """Verify that unauthenticated users can view products and categories."""
        response_cats = self.client.get(self.category_list_url)
        self.assertEqual(response_cats.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_cats.data), 1)

        response_prods = self.client.get(self.product_list_url)
        self.assertEqual(response_prods.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_prods.data), 1)

    def test_customer_cannot_create_product(self):
        """Verify that customer role cannot write categories or products."""
        self.client.force_authenticate(user=self.customer)
        data = {
            'category': self.category.id,
            'name': 'Laptop Y',
            'price': 999.99,
            'stock': 10
        }
        response = self.client.post(self.product_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_create_product(self):
        """Verify that manager role can write categories and products."""
        self.client.force_authenticate(user=self.manager)
        data = {
            'category': self.category.id,
            'name': 'Laptop Y',
            'price': 999.99,
            'stock': 10
        }
        response = self.client.post(self.product_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_cart_management(self):
        """Test standard customer cart workflow and stock validation."""
        self.client.force_authenticate(user=self.customer)
        
        # Add to cart
        data = {'product': self.product.id, 'quantity': 2}
        response = self.client.post(self.cart_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.filter(user=self.customer).count(), 1)
        
        # Adding more than stock should fail
        data_over = {'product': self.product.id, 'quantity': 10}
        response_over = self.client.post(self.cart_list_url, data_over)
        self.assertEqual(response_over.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_creation_and_stock_reduction(self):
        """Test order checkout workflow: total price, stock deduction, clearing cart."""
        self.client.force_authenticate(user=self.customer)
        
        # Add to cart
        CartItem.objects.create(user=self.customer, product=self.product, quantity=2)
        
        # Checkout (Create Order)
        response = self.client.post(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order details
        from decimal import Decimal
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_price, Decimal('999.98')) # 2 * 499.99
        self.assertEqual(order.items.count(), 1)
        
        # Verify stock was decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3) # 5 - 2
        
        # Verify cart was cleared
        self.assertEqual(CartItem.objects.filter(user=self.customer).count(), 0)

    def test_order_cancellation_returns_stock(self):
        """Test that canceling an order restores the items to stock."""
        # Create order
        self.client.force_authenticate(user=self.customer)
        CartItem.objects.create(user=self.customer, product=self.product, quantity=3)
        response_order = self.client.post(self.order_list_url)
        self.assertEqual(response_order.status_code, status.HTTP_201_CREATED)
        
        order_id = response_order.data['id']
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2) # 5 - 3
        
        # Customer cannot cancel directly via API status update (needs manager permission)
        self.client.force_authenticate(user=self.customer)
        order_detail_url = reverse('order-detail', args=[order_id])
        response_cancel_cust = self.client.patch(order_detail_url, {'status': 'canceled'})
        self.assertEqual(response_cancel_cust.status_code, status.HTTP_403_FORBIDDEN)
        
        # Manager cancels order
        self.client.force_authenticate(user=self.manager)
        response_cancel_mgr = self.client.patch(order_detail_url, {'status': 'canceled'})
        self.assertEqual(response_cancel_mgr.status_code, status.HTTP_200_OK)
        
        # Verify stock returned
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5) # Stock returned to 5

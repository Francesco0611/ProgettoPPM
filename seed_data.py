import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Category, Product, Order, OrderItem

User = get_user_model()

def seed():
    print("Seeding database...")
    
    # 1. Create demo users
    print("Creating demo accounts...")
    
    # Admin / Superuser
    if not User.objects.filter(username='admin_demo').exists():
        admin = User.objects.create_superuser(
            username='admin_demo',
            email='admin@example.com',
            password='admin12345',
            role='admin'
        )
        print(f"Created admin user: {admin}")
    
    # Store Manager
    if not User.objects.filter(username='manager_demo').exists():
        manager = User.objects.create_user(
            username='manager_demo',
            email='manager@example.com',
            password='manager12345',
            role='manager'
        )
        print(f"Created manager user: {manager}")

    # Customer
    if not User.objects.filter(username='user_demo').exists():
        customer = User.objects.create_user(
            username='user_demo',
            email='customer@example.com',
            password='user12345',
            role='customer'
        )
        print(f"Created customer user: {customer}")

    # 2. Create Categories
    print("Creating categories...")
    electronics, _ = Category.objects.get_or_create(
        name='Electronics',
        description='Gadgets, devices, and accessories.'
    )
    clothing, _ = Category.objects.get_or_create(
        name='Clothing',
        description='Fashionable clothes for everyone.'
    )
    books, _ = Category.objects.get_or_create(
        name='Books',
        description='Fictional, educational, and professional literature.'
    )
    
    # 3. Create Products
    print("Creating products...")
    laptop, _ = Product.objects.get_or_create(
        category=electronics,
        name='SuperBook Pro 15',
        price=1299.99,
        stock=10,
        description='A powerful professional laptop with 16GB RAM and 512GB SSD.'
    )
    phone, _ = Product.objects.get_or_create(
        category=electronics,
        name='Galaxy Nexus Z',
        price=799.49,
        stock=25,
        description='Next-gen smartphone with premium camera.'
    )
    tshirt, _ = Product.objects.get_or_create(
        category=clothing,
        name='Classic Cotton T-Shirt',
        price=19.99,
        stock=100,
        description='100% organic cotton basic t-shirt in Navy Blue.'
    )
    book, _ = Product.objects.get_or_create(
        category=books,
        name='Designing Data-Intensive Applications',
        price=45.00,
        stock=5,
        description='The definitive guide to data systems architecture.'
    )
    
    print(f"Created categories and products.")

    # 4. Create a past order for customer (to make it look populated)
    print("Creating sample orders...")
    customer_user = User.objects.get(username='user_demo')
    if not Order.objects.filter(user=customer_user).exists():
        # Sample order 1: delivered
        order1 = Order.objects.create(
            user=customer_user,
            status='delivered',
            total_price=839.48
        )
        OrderItem.objects.create(
            order=order1,
            product=phone,
            quantity=1,
            price_at_order=799.49
        )
        OrderItem.objects.create(
            order=order1,
            product=tshirt,
            quantity=2,
            price_at_order=19.99
        )
        
        # Sample order 2: pending
        order2 = Order.objects.create(
            user=customer_user,
            status='pending',
            total_price=45.00
        )
        OrderItem.objects.create(
            order=order2,
            product=book,
            quantity=1,
            price_at_order=45.00
        )
        
        print("Created sample orders.")
    
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()

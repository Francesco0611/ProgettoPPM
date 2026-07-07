from rest_framework import serializers
from django.db import transaction
from .models import Category, Product, CartItem, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')
        read_only_fields = ('slug',)

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'category', 'category_name', 'name', 'slug', 'description', 'price', 'stock', 'is_active', 'is_available')
        read_only_fields = ('slug',)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_detail', 'quantity', 'total_price')

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)

        if not product.is_active:
            raise serializers.ValidationError({"product": "This product is no longer active."})

        if quantity > product.stock:
            raise serializers.ValidationError({"quantity": f"Only {product.stock} units of this product are in stock."})

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)

        # Check if the item already exists in the cart
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            total_qty = cart_item.quantity + quantity
            if total_qty > product.stock:
                raise serializers.ValidationError({"quantity": f"Only {product.stock} units are in stock. You already have {cart_item.quantity} in your cart."})
            cart_item.quantity = total_qty
            cart_item.save()

        return cart_item

    def update(self, instance, validated_data):
        quantity = validated_data.get('quantity', instance.quantity)
        if quantity > instance.product.stock:
            raise serializers.ValidationError({"quantity": f"Only {instance.product.stock} units are in stock."})
        instance.quantity = quantity
        instance.save()
        return instance

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, default='Deleted Product')
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'price_at_order', 'total_price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'user_username', 'status', 'created_at', 'updated_at', 'total_price', 'items')
        read_only_fields = ('user', 'status', 'total_price')

    def create(self, validated_data):
        user = self.context['request'].user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            raise serializers.ValidationError("Your cart is empty.")

        with transaction.atomic():
            # Check availability and stock for all cart items first
            for item in cart_items:
                if not item.product.is_active:
                    raise serializers.ValidationError(f"Product '{item.product.name}' is no longer active.")
                if item.quantity > item.product.stock:
                    raise serializers.ValidationError(f"Insufficient stock for '{item.product.name}'. Only {item.product.stock} units left.")

            # Create the order
            order = Order.objects.create(user=user, total_price=0)
            total_price = 0

            # Process order items and update stocks
            for item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_order=item.product.price
                )
                total_price += order_item.total_price

                # Decrement stock
                item.product.stock -= item.quantity
                item.product.save()

            order.total_price = total_price
            order.save()

            # Clear cart
            cart_items.delete()

        return order

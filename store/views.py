from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from users.permissions import IsStoreManager, IsCustomer
from .models import Category, Product, CartItem, Order
from .serializers import (
    CategorySerializer, ProductSerializer, CartItemSerializer, OrderSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsStoreManager]
        return [permission() for permission in permission_classes]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsStoreManager]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = Product.objects.all()
        # Optional category filtering by ID or Slug
        category_param = self.request.query_params.get('category', None)
        if category_param is not None:
            if category_param.isdigit():
                queryset = queryset.filter(category_id=category_param)
            else:
                queryset = queryset.filter(category__slug=category_param)
        
        # Optional search by name or description
        search_param = self.request.query_params.get('search', None)
        if search_param is not None:
            queryset = queryset.filter(
                Q(name__icontains=search_param) | Q(description__icontains=search_param)
            )

        # Customers should only see active products
        user = self.request.user
        is_manager = user and user.is_authenticated and (user.role in ['manager', 'admin'] or user.is_superuser)
        if not is_manager:
            queryset = queryset.filter(is_active=True)

        return queryset

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsCustomer]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsStoreManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role in ['manager', 'admin']:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        status_value = request.data.get('status')
        if not status_value:
            return Response({"status": "This field is required for updating an order."}, status=status.HTTP_400_BAD_REQUEST)
        
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if status_value not in valid_statuses:
            return Response({"status": f"Invalid status. Must be one of {valid_statuses}."}, status=status.HTTP_400_BAD_REQUEST)

        # Handle stock replenishment upon cancellation
        if status_value == 'canceled' and instance.status != 'canceled':
            for item in instance.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()
        # If it was canceled and gets changed back, subtract stock again (if stock is available)
        elif instance.status == 'canceled' and status_value != 'canceled':
            for item in instance.items.all():
                if item.product:
                    if item.product.stock < item.quantity:
                        return Response({"detail": f"Cannot restore order. Insufficient stock for product '{item.product.name}'."}, status=status.HTTP_400_BAD_REQUEST)
                    item.product.stock -= item.quantity
                    item.product.save()

        instance.status = status_value
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# store/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Product, Cart, Order
from .serializers import ProductSerializer, CartSerializer, OrderSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated  
from rest_framework.decorators import action

from django.shortcuts import render
from .models import Product

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    # Filtering products by category (Men, Women, Kids)
    @action(detail=False, methods=['get'])
    def category_filter(self, request):
        category = request.query_params.get('category', None)
        if category:
            products = Product.objects.filter(category=category)
        else:
            products = Product.objects.all()
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)



# Cart ViewSet
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access their cart

    def create(self, request, *args, **kwargs):
        """Add product to cart."""
        user = request.user
        product_id = request.data.get('product')
        quantity = request.data.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create or update the cart item
        cart_item, created = Cart.objects.get_or_create(user=user, product=product)
        cart_item.quantity += quantity
        cart_item.save()

        return Response(CartSerializer(cart_item).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Remove product from cart."""
        cart_item = self.get_object()
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Order ViewSet
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access

    def create(self, request, *args, **kwargs):
        """Create a new order from the cart."""
        products = request.data.get('products')  # List of product IDs
        total_price = request.data.get('total_price')
        
        # Get the authenticated user
        user = request.user

        # Create the order
        order = Order.objects.create(user=user, total_price=total_price, status='Pending')
        
        # Add the products to the order
        for product_id in products:
            product = Product.objects.get(id=product_id)
            order.products.add(product)
        
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update an existing order status."""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['Pending', 'Shipped', 'Delivered', 'Cancelled']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        return Response(OrderSerializer(order).data)

    def destroy(self, request, *args, **kwargs):
        """Delete an order."""
        order = self.get_object()
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Signup View
class SignupView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new user
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # Generate JWT tokens
        token = RefreshToken.for_user(user)
        return Response({
            'refresh': str(token),
            'access': str(token.access_token),
        }, status=status.HTTP_201_CREATED)


#   all for template rendering

def home(request):
    # You can pass data to the template (like trending products)
    trending_products = Product.objects.all()[:5]  # Get the top 5 products
    return render(request, 'store/home.html', {'products': trending_products})

def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def cart(request):
    return render(request, 'store/cart.html')

def order_history(request):
    return render(request, 'store/order_history.html')
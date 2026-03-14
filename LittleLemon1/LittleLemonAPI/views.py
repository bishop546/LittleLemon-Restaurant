from django.shortcuts import render
from rest_framework import viewsets, generics, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, MenuItem, Cart, Order, OrderItem
from .permissions import IsAdminOrManager, IsAdmin, IsManagerOrCrewOrCustomer, IsManagerOrCustomer
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, RegisterSerializer
from .serializers import LoginSerializer, UserSerializer, GroupSerializer, GroupMembershipSerializer, ManagerMembershipSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, DjangoModelPermissions, IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.decorators import action

class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['slug', 'title']
    search_fields = ['slug', 'title']
    ordering_fields = ['slug', 'title']
    permission_classes = [IsAuthenticatedOrReadOnly, DjangoModelPermissions]

class MenuItemView(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['title', 'price', 'featured', 'category']
    search_fields = ['title']
    ordering_fields = ['title', 'price']
    permission_classes = [IsAuthenticatedOrReadOnly, DjangoModelPermissions]

class CartView(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'menuitem']
    search_fields = ['user__username']
    ordering_fields = ['user__username', 'menuitem__title']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # 1. If the user is a Manager or Superuser, show ALL cart items
        if user.is_superuser or user.groups.filter(name='Managers').exists():
            return Cart.objects.all()
        # 2. For any other user (like a Customer), show only their own cart items
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set the user to the logged-in user when creating a cart item
        serializer.save(user=self.request.user)

    def update(self, serializer):
        # Ensure that the user cannot change the 'user' field of the cart item
        serializer.save(user=self.request.user)

    # To clear the WHOLE cart (Bulk Delete), it's best to use a custom action
    # or override the 'destroy' method carefully.
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response({"detail": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT)

class OrderView(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'status']
    search_fields = ['user__username']
    ordering_fields = ['user__username', 'status']
    permission_classes = [IsManagerOrCrewOrCustomer]

    def get_queryset(self):
        user = self.request.user
        # 1. If the user is a Manager or Superuser, show ALL orders
        if user.is_superuser or user.groups.filter(name='Managers').exists():
            return Order.objects.all()
        # 2. If the user is Delivery Crew, show ONLY orders assigned to them
        if user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        # 3. For any other user (like a Customer), show only their own orders
        return Order.objects.filter(user=user)

    def partial_update(self, request, *args, **kwargs):
        user = self.request.user
        is_manager = user.is_superuser or user.groups.filter(name='Managers').exists()
        is_delivery_crew = user.groups.filter(name='Delivery Crew').exists()
        
        # 1. SECURITY CHECK: If user is Delivery Crew, restrict what they can PATCH
        if is_delivery_crew and not is_manager:
            # If they try to send anything other than 'status', block it
            # This is like a selective receptor only allowing one specific ligand
            allowed_fields = {'status'}
            sent_fields = set(request.data.keys())
            
            if not sent_fields.issubset(allowed_fields):
                return Response(
                    {"detail": "Delivery crew can only update the order status."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # 2. MANAGER LOGIC: Assignment by username
        crew_username = request.data.get('delivery_crew')
        if crew_username:
            if not is_manager:
                return Response(
                    {"detail": "Only managers can assign delivery crew."},
                    status=status.HTTP_403_FORBIDDEN
                )
            try:
                crew_member = User.objects.get(
                    username=crew_username, 
                    groups__name='Delivery Crew'
                )            
                request.data['delivery_crew'] = crew_member.id
            except User.DoesNotExist:
                return Response(
                    {"detail": f"Delivery crew member '{crew_username}' not found or invalid."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return super().partial_update(request, *args, **kwargs)
    
    def create(self, request):
        """ The 'Checkout' Procedure """
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        
        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic(): # Ensure the surgery is successful before finishing
            total = sum(item.price for item in cart_items)
            order = Order.objects.create(user=user, total=total, status=False)

            # Transplanting items from Cart to OrderItem
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price
                )
            # Post-Op: Clear the Cart
            cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderItemView(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['order', 'menuitem']
    search_fields = ['order__user__username', 'menuitem__title']
    ordering_fields = ['order__user__username', 'menuitem__title']
    permission_classes = [IsAuthenticatedOrReadOnly, DjangoModelPermissions]

class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class GroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser, DjangoModelPermissions]

class Item_Of_The_DayView(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, DjangoModelPermissions]

    def get_queryset(self):
        # When just "listing" (GET /api/item-of-the-day/), only show featured
        if self.action == 'list':
            return MenuItem.objects.filter(featured=True)
        # For PATCH, DELETE, or RETRIEVE by ID, allow all
        return MenuItem.objects.all()

# Views for user registration
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# Views for user login
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class GroupMembershipView(APIView):
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        """Add users to a group"""
        serializer = GroupMembershipSerializer(data=request.data)
        if serializer.is_valid():
            group = Group.objects.get(name=serializer.validated_data['group_name'])
            users = User.objects.filter(username__in=serializer.validated_data['usernames'])
            for user in users:
                group.user_set.add(user)
            return Response({"message": "Users added successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Remove users from a group"""
        serializer = GroupMembershipSerializer(data=request.data)
        if serializer.is_valid():
            group = Group.objects.get(name=serializer.validated_data['group_name'])
            users = User.objects.filter(username__in=serializer.validated_data['usernames'])
            for user in users:
                group.user_set.remove(user)
            return Response({"message": "Users removed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ManagerMembershipView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        """Add users to a group"""
        serializer = ManagerMembershipSerializer(data=request.data)
        if serializer.is_valid():
            group = Group.objects.get(name=serializer.validated_data['group_name'])
            users = User.objects.filter(username__in=serializer.validated_data['usernames'])
            for user in users:
                group.user_set.add(user)
            return Response({"message": "Users added successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Remove users from a group"""
        serializer = ManagerMembershipSerializer(data=request.data)
        if serializer.is_valid():
            group = Group.objects.get(name=serializer.validated_data['group_name'])
            users = User.objects.filter(username__in=serializer.validated_data['usernames'])
            for user in users:
                group.user_set.remove(user)
            return Response({"message": "Users removed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']

class CategorySerializer(serializers.ModelSerializer):
    menu_items = MenuItemSerializer(many=True, read_only=True) # to get the menu items in the category
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title', 'menu_items'] # if you add menu_items, it gives you the menu items in the category. Ensure that the related_name in the MenuItem model is set to 'menu_items' for this to work

class CartSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True) # to show the username instead of the user id
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True) # to show the price of the menu item at the time it was added to the cart
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True) # to show the total price for the quantity of the menu item in the cart
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menu_item', 'quantity', 'unit_price', 'price']

    def validate(self, attrs):
        # Calculation happens here before saving
        menu_item = attrs.get('menu_item')
        quantity = attrs.get('quantity')     
        # Inject calculated values into the validated data 'stream'
        attrs['unit_price'] = menu_item.price
        attrs['price'] = menu_item.price * quantity
        return attrs

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class GroupSerializer(serializers.ModelSerializer):
    users = UserSerializer(source='user_set', many=True)
    class Meta:
        model = Group
        fields = ['id', 'name', 'users'] # if you add user_set, it gives you the users in the group, but 'users' is more intuitive than 'user_set'


# Serializer for user registration
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

# Serializer for user login
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return {'user': user, 'token': token.key}
        raise serializers.ValidationError("Invalid credentials")
    

class GroupMembershipSerializer(serializers.Serializer):
    group_name = serializers.CharField()
    usernames = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )

    def validate_group_name(self, value):
        try:
            Group.objects.get(name=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Group does not exist.")
        return value

    def validate_usernames(self, value):
        users = User.objects.filter(username__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("One or more users do not exist.")
        return value

class ManagerMembershipSerializer(serializers.Serializer):
    group_name = serializers.CharField()
    usernames = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )

    def validate_group_name(self, value):
        try:
            Group.objects.get(name=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Group does not exist.")
        return value

    def validate_usernames(self, value):
        users = User.objects.filter(username__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("One or more users do not exist.")
        return value

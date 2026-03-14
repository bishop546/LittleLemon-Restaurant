from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryView, GroupMembershipView, ManagerMembershipView, Item_Of_The_DayView
from .views import MenuItemView, CartView, OrderView, OrderItemView, RegisterView, LoginView, UserView, GroupView
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'categories', CategoryView)
router.register(r'item-of-the-day', Item_Of_The_DayView, basename='item-of-the-day')
router.register(r'groups', GroupView)
router.register(r'users', UserView)
router.register(r'menu-items', MenuItemView)
router.register(r'carts/menu-items', CartView, basename='carts')
router.register(r'orders', OrderView)
router.register(r'order-items', OrderItemView)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    path('token/register/', RegisterView.as_view(), name='register'),
    path('token/login/', LoginView.as_view(), name='login'),
    path('group/membership/', GroupMembershipView.as_view(), name='group-membership'),
    path('manager/membership/', ManagerMembershipView.as_view(), name='manager-membership'),
]
from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsAdminOrManager(BasePermission):
    """
    Allows access only to admins (is_staff) or users in the 'managers' group.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.groups.filter(name="Manager").exists()

class IsAdmin(BasePermission):
    """
    Allows access only to admins (is_staff) or users in the 'managers' group.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser
    
class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Check if the user is even logged in (Authenticated)
        if not request.user or not request.user.is_authenticated:
            return False
        # 2. Allow if they are a Superuser (The Master Key)
        if request.user.is_superuser:
            return True
        # 3. Allow if they are in the 'Managers' group (The Specific Badge)
        return request.user.groups.filter(name='Managers').exists()

class IsManagerOrCrewOrCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. User must be authenticated
        if not request.user.is_authenticated:
            return False         
        # 2. Managers/Superusers can do anything (GET, POST, PATCH, DELETE)
        if request.user.is_superuser or request.user.groups.filter(name='Managers').exists():
            return True         
        # 3. Delivery Crew and Customers can only READ or PATCH (update status)
        # We handle specific field restrictions in the view logic
        if request.method in permissions.SAFE_METHODS or request.method == 'PATCH':
            return True        
        return False

class IsManagerOrCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. User must be authenticated
        if not request.user.is_authenticated:
            return False         
        # 2. Managers/Superusers can do anything (GET, POST, PATCH, DELETE)
        if request.user.is_superuser or request.user.groups.filter(name='Managers').exists():
            return True         
        # 3. Allow Customers to POST (add to cart) and DELETE (clear cart) 
        # as well as GET and PATCH
        allowed_methods = ['GET', 'POST', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
        if request.method in allowed_methods:
            return True        
            
        return False
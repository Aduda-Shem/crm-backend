from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.crm.models import Lead, Contact


class IsManagerOrNoDeleteForAgents(BasePermission):
    """
        Managers have full access; agents cannot delete leads/contacts.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Managers can do anything
        if getattr(request.user, 'is_manager', lambda: False)():
            return True
        # Agents cannot delete Lead or Contact
        if request.method == 'DELETE':
            return not isinstance(obj, (Lead, Contact))
        return True



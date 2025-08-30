"""
Audit service for creating audit trail entries.
"""

from apps.crm.models import AuditTrail
from decimal import Decimal
from datetime import datetime


def make_serializable(value):
    """
    Recursively convert Decimals and datetimes to JSON-serializable types.
    """
    if isinstance(value, dict):
        return {k: make_serializable(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [make_serializable(v) for v in value]
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    return value


def create_audit_entry(user, action, instance, old_value=None, ip_address=None, user_agent=None):
    if hasattr(instance, 'get_serializer'):
        new_value = instance.get_serializer(instance).data
    else:
        # Fallback serialization
        new_value = {
            'id': instance.id,
            'model': instance._meta.model_name,
        }
        # Add common fields if they exist
        for field in ['name', 'title', 'content', 'message']:
            if hasattr(instance, field):
                new_value[field] = getattr(instance, field)
    
    # Make old_value and new_value JSON-serializable
    old_value = make_serializable(old_value)
    new_value = make_serializable(new_value) if action != 'delete' else None

    AuditTrail.objects.create(
        user=user,
        action=action,
        model=instance._meta.label,
        object_id=str(instance.pk),
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

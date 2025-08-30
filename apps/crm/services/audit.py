"""
Audit service for creating audit trail entries.
"""

from apps.crm.models import AuditTrail


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
    
    AuditTrail.objects.create(
        user=user,
        action=action,
        model=instance._meta.label,
        object_id=str(instance.pk),
        old_value=old_value,
        new_value=None if action == 'delete' else new_value,
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

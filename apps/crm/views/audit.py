from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.crm.models import AuditTrail
from apps.crm.serializers import AuditEntrySerializer
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q


class AuditGenericAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuditEntrySerializer

    def get(self, request):
        user = request.query_params.get('user')
        model = request.query_params.get('model')
        action = request.query_params.get('action')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        page = int(request.query_params.get('page', 1))
        rows = int(request.query_params.get('rows', 25))

        query = Q(pk__isnull=False)

        if user:
            query &= Q(user_id=user)
        if model:
            query &= Q(model__icontains=model)
        if action:
            query &= Q(action__iexact=action)
        if date_from:
            query &= Q(created_at__gte=date_from)
        if date_to:
            query &= Q(created_at__lte=date_to)

        # Filter by user role
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            query &= Q(user=request.user)

        audit_entries = AuditTrail.objects.filter(query).select_related('user').order_by('-created_at')

        paginator = Paginator(audit_entries, rows)
        audit_page = paginator.page(page)

        # Format results for response
        results = []
        for entry in audit_page:
            def truncate_val(val, length=65):
                if not val:
                    return "—"
                val_str = str(val)
                return val_str if len(val_str) <= length else val_str[:length] + "…"

            results.append({
                'id': entry.id,
                'user': getattr(entry.user, 'username', None),
                'action': entry.action,
                'model': entry.model,
                'object_id': entry.object_id,
                'old_value': truncate_val(entry.old_value, 65),
                'new_value': truncate_val(entry.new_value, 65),
                'ip_address': entry.ip_address,
                'user_agent': entry.user_agent,
                'timestamp': entry.created_at,
            })


        # Validate with serializer for schema consistency
        serializer = self.get_serializer(results, many=True)

        return Response({
            'message': "Audit Trail Fetched Successfully",
            "audit_entries": serializer.data,
            "current_page": page,
            "last_page": paginator.num_pages,
            "total": paginator.count,
        }, status=status.HTTP_200_OK)

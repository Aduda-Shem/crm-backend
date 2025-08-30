from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.crm.models import Lead, Contact, Note, Reminder, Correspondence, AuditTrail
from apps.crm.serializers import (
    LeadSerializer,
    ContactSerializer,
    NoteSerializer,
    ReminderSerializer,
    CorrespondenceSerializer,
    AuditEntrySerializer
)

class DashboardAPIView(generics.GenericAPIView):
    """
    Aggregated CRM dashboard: counts, recent activity, chart data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Optional filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_id = request.query_params.get('user_id')

        # Base filter
        base_filter = Q()
        if start_date:
            base_filter &= Q(created_at__gte=start_date)
        if end_date:
            base_filter &= Q(created_at__lte=end_date)
        if user_id:
            base_filter &= Q(owner_id=user_id) | Q(created_by_id=user_id) | Q(user_id=user_id)

        # Counts
        counts = {
            'leads_total': Lead.objects.filter(base_filter).count(),
            'contacts_total': Contact.objects.filter(base_filter).count(),
            'notes_total': Note.objects.filter(base_filter).count(),
            'reminders_total': Reminder.objects.filter(base_filter).count(),
            'correspondence_total': Correspondence.objects.filter(base_filter).count(),
            'audit_entries_total': AuditTrail.objects.filter(base_filter).count(),
        }

        # Recent activity (limit 5 each)
        recent_data = {
            'leads': LeadSerializer(Lead.objects.filter(base_filter).order_by('-created_at')[:5], many=True).data,
            'contacts': ContactSerializer(Contact.objects.filter(base_filter).order_by('-created_at')[:5], many=True).data,
            'notes': NoteSerializer(Note.objects.filter(base_filter).order_by('-created_at')[:5], many=True).data,
            'reminders': ReminderSerializer(Reminder.objects.filter(base_filter).order_by('-created_at')[:5], many=True).data,
            'correspondence': CorrespondenceSerializer(Correspondence.objects.filter(base_filter).order_by('-created_at')[:5], many=True).data,
            'audit_entries': AuditEntrySerializer(AuditTrail.objects.filter(base_filter).select_related('user').order_by('-created_at')[:5], many=True).data,
        }

        # Chart data
        charts = {
            'leads_by_status': list(Lead.objects.filter(base_filter).values('status').annotate(count=Count('id'))),
            'reminders_by_status': list(Reminder.objects.filter(base_filter).values('status').annotate(count=Count('id'))),
        }

        return Response({
            'message': "Dashboard data fetched successfully",
            'counts': counts,
            'recent': recent_data,
            'charts': charts,
        }, status=status.HTTP_200_OK)

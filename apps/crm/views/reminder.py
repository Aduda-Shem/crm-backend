from apps.crm.models.lead import Lead
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.crm.models import Reminder
from apps.crm.serializers import ReminderSerializer
from apps.crm.services.audit import create_audit_entry, get_client_ip
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.utils import timezone
from dateutil import parser 

class ReminderGenericAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReminderSerializer


    def get(self, request):
        lead = request.query_params.get('lead')
        status_q = request.query_params.get('status')
        reminder_type = request.query_params.get('reminder_type')
        created_by = request.query_params.get('created_by')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        rows = int(request.query_params.get('rows', 25))

        query = Q(pk__isnull=False)

        if lead:
            query &= Q(lead_id=lead)
        if status_q:
            query &= Q(status=status_q)
        if reminder_type:
            query &= Q(reminder_type=reminder_type)
        if created_by:
            query &= Q(created_by_id=created_by)
        if search:
            query &= Q(message__icontains=search)

        # Filter by user role
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            query &= Q(lead__owner=request.user)

        reminders = Reminder.objects.filter(query).order_by('scheduled_time')

        paginator = Paginator(reminders, rows)
        reminders_page = paginator.page(page)

        return Response({
            'message': "Reminders Fetched Successfully",
            "reminders": self.serializer_class(reminders_page, many=True).data,
            "current_page": page,
            "last_page": paginator.num_pages,
            "total": paginator.count,
        }, status=status.HTTP_200_OK)

 

    def post(self, request):
        lead_id = request.data.get('lead_id')
        message = request.data.get('message')
        scheduled_time_str = request.data.get('scheduled_time')
        reminder_type = request.data.get('reminder_type', 'FOLLOW_UP')

        # Required fields validation
        if not lead_id or not message or not scheduled_time_str:
            return Response(
                {'error': 'Lead, message, and scheduled_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lead exists & access check
        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        if getattr(request.user, 'is_agent', lambda: False)() and lead.owner != request.user:
            return Response({'error': 'You can only create reminders for your own leads'}, status=status.HTTP_403_FORBIDDEN)

        # Parse scheduled_time as aware datetime
        try:
            scheduled_time = parser.isoparse(scheduled_time_str)
            if timezone.is_naive(scheduled_time):
                scheduled_time = timezone.make_aware(scheduled_time, timezone.get_default_timezone())
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid scheduled_time format. Use ISO format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate scheduled_time is in the future
        if scheduled_time <= timezone.now():
            return Response(
                {'error': 'Scheduled time must be in the future'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create reminder
        reminder = Reminder(
            lead=lead,
            message=message,
            scheduled_time=scheduled_time,
            reminder_type=reminder_type,
            status='PENDING',
            created_by=request.user
        )
        reminder.save()

        # Audit entry
        create_audit_entry(
            user=request.user,
            action='create',
            instance=reminder,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response(
            {'message': 'Reminder created successfully', 'reminder': self.serializer_class(reminder).data},
            status=status.HTTP_201_CREATED
        )


    def put(self, request):
        reminder_id = request.data.get('id') or request.query_params.get('id')
        reminder = Reminder.objects.filter(pk=reminder_id).first()

        if not reminder:
            return Response({
                'error': 'Reminder not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and reminder.lead.owner != request.user:
            return Response({
                'error': 'You can only update reminders for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'message': reminder.message,
            'scheduled_time': reminder.scheduled_time,
            'reminder_type': reminder.reminder_type,
            'status': reminder.status
        }

        reminder.message = request.data.get('message', reminder.message)
        reminder.reminder_type = request.data.get('reminder_type', reminder.reminder_type)
        
        # Update scheduled time if provided
        if request.data.get('scheduled_time'):
            try:
                new_scheduled_time = timezone.datetime.fromisoformat(
                    request.data.get('scheduled_time').replace('Z', '+00:00')
                )
                if new_scheduled_time <= timezone.now():
                    return Response({
                        'error': 'Scheduled time must be in the future'
                    }, status=status.HTTP_400_BAD_REQUEST)
                reminder.scheduled_time = new_scheduled_time
            except ValueError:
                return Response({
                    'error': 'Invalid scheduled_time format. Use ISO format.'
                }, status=status.HTTP_400_BAD_REQUEST)

        reminder.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='update',
            instance=reminder,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Reminder updated successfully',
            'reminder': self.serializer_class(reminder).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        reminder_id = request.query_params.get('id')
        reminder = Reminder.objects.filter(pk=reminder_id).first()

        if not reminder:
            return Response({
                'error': 'Reminder not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and reminder.lead.owner != request.user:
            return Response({
                'error': 'You can only delete reminders for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'message': reminder.message,
            'scheduled_time': reminder.scheduled_time,
            'reminder_type': reminder.reminder_type,
            'status': reminder.status
        }

        # Create audit entry before deletion
        create_audit_entry(
            user=request.user,
            action='delete',
            instance=reminder,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        reminder.delete()

        return Response({
            'message': 'Reminder deleted successfully'
        }, status=status.HTTP_200_OK)

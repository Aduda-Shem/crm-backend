from apps.crm.models.contact import Contact

from apps.crm.models import Correspondence
from apps.crm.serializers import CorrespondenceSerializer
from apps.crm.services.audit import create_audit_entry, get_client_ip
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q


class CorrespondenceGenericAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CorrespondenceSerializer

    def get(self, request):
        contact = request.query_params.get('contact')
        type_q = request.query_params.get('type')
        created_by = request.query_params.get('created_by')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        rows = int(request.query_params.get('rows', 25))

        query = Q(pk__isnull=False)

        if contact:
            query &= Q(contact_id=contact)
        if type_q:
            query &= Q(type=type_q)
        if created_by:
            query &= Q(created_by_id=created_by)
        if search:
            query &= Q(
                Q(notes__icontains=search) |
                Q(outcome__icontains=search)
            )

        # Filter by user role
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            query &= Q(contact__linked_lead__owner=request.user)

        correspondence = Correspondence.objects.filter(query).order_by('-created_at')

        paginator = Paginator(correspondence, rows)
        correspondence_page = paginator.page(page)

        return Response({
            'message': "Correspondence Fetched Successfully",
            "correspondence": self.serializer_class(correspondence_page, many=True).data,
            "current_page": page,
            "last_page": paginator.num_pages,
            "total": paginator.count,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        contact_id = request.data.get('contact')
        type_q = request.data.get('type')
        notes = request.data.get('notes', '')
        outcome = request.data.get('outcome', '')
        duration = request.data.get('duration')

        # Check if contact exists and user has access
        try:
            contact = Contact.objects.get(pk=contact_id)
            if hasattr(request.user, 'is_agent') and request.user.is_agent() and contact.linked_lead.owner != request.user:
                return Response({
                    'error': 'You can only create correspondence for your own leads'
                }, status=status.HTTP_403_FORBIDDEN)
        except Contact.DoesNotExist:
            return Response({
                'error': 'Contact not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate duration for calls and meetings
        if duration is not None and type_q in ['call', 'meeting']:
            duration = int(duration)
            if duration <= 0:
                return Response({
                    'error': 'Duration must be positive for calls and meetings'
                }, status=status.HTTP_400_BAD_REQUEST)


        correspondence = Correspondence()
        correspondence.contact = contact
        correspondence.type = type_q
        correspondence.notes = notes
        correspondence.outcome = outcome
        correspondence.duration = duration
        correspondence.created_by = request.user
        correspondence.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='create',
            instance=correspondence,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Correspondence created successfully',
            'correspondence': self.serializer_class(correspondence).data,
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        correspondence_id = request.data.get('id') or request.query_params.get('id')
        correspondence = Correspondence.objects.filter(pk=correspondence_id).first()

        if not correspondence:
            return Response({
                'error': 'Correspondence not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and correspondence.contact.linked_lead.owner != request.user:
            return Response({
                'error': 'You can only update correspondence for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'type': correspondence.type,
            'notes': correspondence.notes,
            'outcome': correspondence.outcome,
            'duration': correspondence.duration
        }

        correspondence.type = request.data.get('type', correspondence.type)
        correspondence.notes = request.data.get('notes', correspondence.notes)
        correspondence.outcome = request.data.get('outcome', correspondence.outcome)
        
        # Update duration if provided
        if request.data.get('duration') is not None:
            try:
                new_duration = int(request.data.get('duration'))
                if new_duration <= 0:
                    return Response({
                        'error': 'Duration must be positive'
                    }, status=status.HTTP_400_BAD_REQUEST)
                correspondence.duration = new_duration
            except ValueError:
                return Response({
                    'error': 'Duration must be a valid integer'
                }, status=status.HTTP_400_BAD_REQUEST)

        correspondence.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='update',
            instance=correspondence,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Correspondence updated successfully',
            'correspondence': self.serializer_class(correspondence).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        correspondence_id = request.query_params.get('id')
        correspondence = Correspondence.objects.filter(pk=correspondence_id).first()

        if not correspondence:
            return Response({
                'error': 'Correspondence not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and correspondence.contact.linked_lead.owner != request.user:
            return Response({
                'error': 'You can only delete correspondence for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'type': correspondence.type,
            'notes': correspondence.notes,
            'outcome': correspondence.outcome,
            'duration': correspondence.duration
        }

        # Create audit entry before deletion
        create_audit_entry(
            user=request.user,
            action='delete',
            instance=correspondence,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        correspondence.delete()

        return Response({
            'message': 'Correspondence deleted successfully'
        }, status=status.HTTP_200_OK)

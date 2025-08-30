from apps.crm.models.lead import Lead
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.crm.models import Note
from apps.crm.serializers import NoteSerializer
from apps.crm.services.audit import create_audit_entry, get_client_ip
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q


class NoteGenericAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NoteSerializer


    def get(self, request):
        lead = request.query_params.get('lead')
        note_type = request.query_params.get('note_type')
        created_by = request.query_params.get('created_by')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        rows = int(request.query_params.get('rows', 25))

        query = Q(pk__isnull=False)

        if lead:
            query &= Q(lead_id=lead)
        if note_type:
            query &= Q(note_type=note_type)
        if created_by:
            query &= Q(created_by_id=created_by)
        if search:
            query &= Q(content__icontains=search)

        # Filter by user role
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            query &= Q(lead__owner=request.user)

        notes = Note.objects.filter(query).order_by('-created_at')

        paginator = Paginator(notes, rows)
        notes_page = paginator.page(page)

        return Response({
            'message': "Notes Fetched Successfully",
            "notes": self.serializer_class(notes_page, many=True).data,
            "current_page": page,
            "last_page": paginator.num_pages,
            "total": paginator.count,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        content = request.data.get('content')
        lead_id = request.data.get('lead')
        note_type = request.data.get('note_type', 'GENERAL')

        # Check if lead exists and user has access
        lead = Lead.objects.get(pk=lead_id)
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and lead.owner != request.user:
            return Response({
                'error': 'You can only create notes for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        note = Note()
        note.content = content
        note.lead = lead
        note.note_type = note_type
        note.created_by = request.user
        note.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='create',
            instance=note,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Note created successfully',
            'note': self.serializer_class(note).data,
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        note_id = request.data.get('id') or request.query_params.get('id')
        note = Note.objects.filter(pk=note_id).first()

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and note.lead.owner != request.user:
            return Response({
                'error': 'You can only update notes for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'content': note.content,
            'note_type': note.note_type
        }

        note.content = request.data.get('content', note.content)
        note.note_type = request.data.get('note_type', note.note_type)
        note.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='update',
            instance=note,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Note updated successfully',
            'note': self.serializer_class(note).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        note_id = request.query_params.get('id')
        note = Note.objects.filter(pk=note_id).first()

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and note.lead.owner != request.user:
            return Response({
                'error': 'You can only delete notes for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'content': note.content,
            'note_type': note.note_type
        }

        # Create audit entry before deletion
        create_audit_entry(
            user=request.user,
            action='delete',
            instance=note,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        note.delete()

        return Response({
            'message': 'Note deleted successfully'
        }, status=status.HTTP_200_OK)

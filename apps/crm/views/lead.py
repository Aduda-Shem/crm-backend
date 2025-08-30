from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.crm.models import Lead
from apps.crm.serializers import LeadSerializer
from apps.crm.permissions import IsManagerOrNoDeleteForAgents
from apps.crm.services.audit import create_audit_entry, get_client_ip
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q


class LeadGenericAPIView(generics.GenericAPIView):
    permission_classes = [IsManagerOrNoDeleteForAgents]
    serializer_class = LeadSerializer


    def get(self, request):
        lead_id = request.query_params.get('id')
        status_q = request.query_params.get('status')
        owner = request.query_params.get('owner')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        rows = int(request.query_params.get('rows', 25))

        query = Q(pk__isnull=False)

        if status_q:
            query &= Q(status=status_q)
        if lead_id:
            query &= Q(pk=lead_id) 
        if owner:
            query &= Q(owner_id=owner)
        if search:
            query &= Q(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(source__icontains=search)
            )

        # Filter by user role
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            query &= Q(owner=request.user)

        leads = Lead.objects.filter(query).order_by('-created_at')

        paginator = Paginator(leads, rows)
        leads_page = paginator.page(page)

        return Response({
            'message': "Leads Fetched Successfully",
            "leads": self.serializer_class(leads_page, many=True).data,
            "current_page": page,
            "last_page": paginator.num_pages,
            "total": paginator.count,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('name')
        lead_status = request.data.get('status', 'NEW') 
        description = request.data.get('description', '')
        value = request.data.get('value')
        source = request.data.get('source', '')

        lead = Lead()
        lead.name = name
        lead.status = lead_status
        lead.description = description
        lead.value = value
        lead.source = source
        lead.owner = request.user
        lead.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='create',
            instance=lead,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Lead created successfully',
            'lead': self.serializer_class(lead).data,
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        lead_id = request.data.get('id') or request.query_params.get('id')
        lead = Lead.objects.filter(pk=lead_id).first()


        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and lead.owner != request.user:
            return Response({
                'error': 'You can only update your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'name': lead.name,
            'status': lead.status,
            'description': lead.description,
            'value': lead.value,
            'source': lead.source
        }

        lead.name = request.data.get('name', lead.name)
        lead.status = request.data.get('status', lead.status)
        lead.description = request.data.get('description', lead.description)
        lead.value = request.data.get('value', lead.value)
        lead.source = request.data.get('source', lead.source)
        lead.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='update',
            instance=lead,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Lead updated successfully',
            'lead': self.serializer_class(lead).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        lead_id = request.query_params.get('id')
        lead = Lead.objects.filter(pk=lead_id).first()

        if not lead:
            return Response({
                'error': 'Lead not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            return Response({
                'error': 'Agents cannot delete leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'name': lead.name,
            'status': lead.status,
            'description': lead.description,
            'value': lead.value,
            'source': lead.source
        }

        # Create audit entry before deletion
        create_audit_entry(
            user=request.user,
            action='delete',
            instance=lead,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        lead.delete()

        return Response({
            'message': 'Lead deleted successfully'
        }, status=status.HTTP_200_OK)


    def summary(self, request, id):
        """
            Get AI-powered summary of lead notes.
        """
        try:
            lead = Lead.objects.get(pk=id)
            
            # Check permissions
            if hasattr(request.user, 'is_agent') and request.user.is_agent() and lead.owner != request.user:
                return Response({
                    'error': 'You can only view summaries for your own leads'
                }, status=status.HTTP_403_FORBIDDEN)
            
            notes = lead.notes.all().order_by('-created_at')
            
            if not notes.exists():
                return Response({
                    'lead': lead.name,
                    'summary': 'No notes available for this lead.',
                    'ai_available': False
                }, status=status.HTTP_200_OK)
            
            # Extract note content for AI processing
            note_contents = [note.content for note in notes]
            
            # Generate AI summary
            from apps.crm.services.ai_summary import summarize_notes
            summary = summarize_notes(note_contents, lead.name)
            
            return Response({
                'lead': lead.name,
                'summary': summary,
                'ai_available': True,
                'notes_count': len(note_contents)
            }, status=status.HTTP_200_OK)
            
        except Lead.DoesNotExist:
            return Response(
                {'error': 'Lead not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error generating summary: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

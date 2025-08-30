from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.crm.models import Contact
from apps.crm.serializers import ContactSerializer
from apps.crm.permissions import IsManagerOrNoDeleteForAgents
from apps.crm.services.audit import create_audit_entry, get_client_ip
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from apps.crm.models import Lead


class ContactGenericAPIView(generics.GenericAPIView):
    permission_classes = [IsManagerOrNoDeleteForAgents]
    serializer_class = ContactSerializer

    def get(self, request):
        linked_lead = request.query_params.get('linked_lead')
        is_primary = request.query_params.get('is_primary')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        rows = int(request.query_params.get('rows', 25))

        query = Q(pk__isnull=False)

        if linked_lead:
            query &= Q(linked_lead_id=linked_lead)
        if is_primary is not None:
            query &= Q(is_primary=is_primary.lower() in ('true', '1', 'yes', 'on'))
        if search:
            query &= Q(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(company__icontains=search) |
                Q(title__icontains=search)
            )

        # Filter by user role
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            query &= Q(linked_lead__owner=request.user)

        contacts = Contact.objects.filter(query).order_by('name')

        paginator = Paginator(contacts, rows)
        contacts_page = paginator.page(page)

        return Response({
            'message': "Contacts Fetched Successfully",
            "contacts": self.serializer_class(contacts_page, many=True).data,
            "current_page": page,
            "last_page": paginator.num_pages,
            "total": paginator.count,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone', '')
        linked_lead_id = request.data.get('linked_lead')
        title = request.data.get('title', '')
        company = request.data.get('company', '')
        is_primary = request.data.get('is_primary', False)


        linked_lead = Lead.objects.get(pk=linked_lead_id)
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and linked_lead.owner != request.user:
            return Response({
                'error': 'You can only create contacts for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)


        contact = Contact()
        contact.name = name
        contact.email = email
        contact.phone = phone
        contact.linked_lead = linked_lead
        contact.title = title
        contact.company = company
        contact.is_primary = is_primary
        contact.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='create',
            instance=contact,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Contact created successfully',
            'contact': self.serializer_class(contact).data,
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        contact_id = request.data.get('id') or request.query_params.get('id')
        contact = Contact.objects.filter(pk=contact_id).first()

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent() and contact.linked_lead.owner != request.user:
            return Response({
                'error': 'You can only update contacts for your own leads'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone,
            'title': contact.title,
            'company': contact.company,
            'is_primary': contact.is_primary
        }

        contact.name = request.data.get('name', contact.name)
        contact.email = request.data.get('email', contact.email)
        contact.phone = request.data.get('phone', contact.phone)
        contact.title = request.data.get('title', contact.title)
        contact.company = request.data.get('company', contact.company)
        contact.is_primary = request.data.get('is_primary', contact.is_primary)
        contact.save()

        # Create audit entry
        create_audit_entry(
            user=request.user,
            action='update',
            instance=contact,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': 'Contact updated successfully',
            'contact': self.serializer_class(contact).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        contact_id = request.query_params.get('id')
        contact = Contact.objects.filter(pk=contact_id).first()

        # Check permissions
        if hasattr(request.user, 'is_agent') and request.user.is_agent():
            return Response({
                'error': 'Agents cannot delete contacts'
            }, status=status.HTTP_403_FORBIDDEN)

        # Store old values for audit
        old_values = {
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone,
            'title': contact.title,
            'company': contact.company,
            'is_primary': contact.is_primary
        }

        # Create audit entry before deletion
        create_audit_entry(
            user=request.user,
            action='delete',
            instance=contact,
            old_value=old_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        contact.delete()

        return Response({
            'message': 'Contact deleted successfully'
        }, status=status.HTTP_200_OK)

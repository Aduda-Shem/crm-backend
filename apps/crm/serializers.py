from rest_framework import serializers
from apps.crm.models import Lead, Contact, Note, Reminder, Correspondence
from apps.accounts.serializers import UserSerializer
from drf_spectacular.utils import extend_schema_field
from django.utils import timezone

class ContactSerializer(serializers.ModelSerializer):
    linked_lead_name = serializers.CharField(source='linked_lead.name', read_only=True)
    created_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    updated_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'email', 'phone', 'linked_lead', 'linked_lead_name',
            'title', 'company', 'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NoteSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    created_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    updated_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    
    class Meta:
        model = Note
        fields = [
            'id', 'content', 'created_by', 'created_by_username', 'lead', 'lead_name',
            'note_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'updated_at']


class ReminderSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    updated_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'lead', 'lead_name', 'message', 'scheduled_time', 'status',
            'reminder_type', 'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def validate_scheduled_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value


class CorrespondenceSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    updated_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    
    class Meta:
        model = Correspondence
        fields = [
            'id', 'contact', 'contact_name', 'type', 'notes', 'outcome',
            'duration', 'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'updated_at']
    
    def validate_duration(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Duration must be positive.")
        return value


class LeadSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    notes = NoteSerializer(many=True, read_only=True)
    reminders = ReminderSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    updated_at = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    
    contacts_count = serializers.SerializerMethodField()
    notes_count = serializers.SerializerMethodField()
    reminders_count = serializers.SerializerMethodField()
    
    # Convert Decimal to float for JSON serialization
    value = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'status', 'owner', 'owner_username', 'description',
            'value', 'source', 'created_at', 'updated_at', 'contacts', 'notes',
            'reminders', 'contacts_count', 'notes_count', 'reminders_count'
        ]
        read_only_fields = ['owner', 'owner_username', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField)
    def get_contacts_count(self, obj):
        return obj.contacts.count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_notes_count(self, obj):
        return obj.notes.count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_reminders_count(self, obj):
        return obj.reminders.count()
    
    @extend_schema_field(serializers.FloatField)
    def get_value(self, obj):
        return float(obj.value) if obj.value is not None else None
    
    def validate_value(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Lead value must be positive.")
        return value

class LeadSummarySerializer(serializers.Serializer):
    """
        Serializer for AI summary response.
    """
    lead = serializers.CharField()
    summary = serializers.CharField()
    ai_available = serializers.BooleanField()
    notes_count = serializers.IntegerField(required=False)


class AuditEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.CharField(allow_null=True, required=False)
    action = serializers.CharField()
    model = serializers.CharField()
    object_id = serializers.CharField()
    old_value = serializers.JSONField(required=False, allow_null=True)
    new_value = serializers.JSONField(required=False, allow_null=True)
    ip_address = serializers.CharField(allow_null=True, required=False)
    user_agent = serializers.CharField(allow_null=True, required=False)



"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.crm.views.audit import AuditGenericAPIView
from apps.crm.views.contact import ContactGenericAPIView
from apps.crm.views.correspondence import CorrespondenceGenericAPIView
from apps.crm.views.lead import LeadGenericAPIView
from apps.crm.views.note import NoteGenericAPIView
from apps.crm.views.reminder import ReminderGenericAPIView
from apps.crm.views.dashboard import DashboardAPIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/leads/', LeadGenericAPIView.as_view(), name='leads'),
    path('api/leads/<int:id>/summary/', LeadGenericAPIView.as_view(), name='lead-summary'),
    path('api/contacts/', ContactGenericAPIView.as_view(), name='contacts'),
    path('api/notes/', NoteGenericAPIView.as_view(), name='notes'),
    path('api/reminders/', ReminderGenericAPIView.as_view(), name='reminders'),
    path('api/correspondence/', CorrespondenceGenericAPIView.as_view(), name='correspondence'),
    path('api/audit/', AuditGenericAPIView.as_view(), name='audit'),
    # Dashboard endpoint
    path('api/dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    
    # JWT Auth endpoints (explicitly defined for clarity)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/auth/', include('apps.accounts.urls')),
]

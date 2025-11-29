from django.urls import path
from . import views
from .views import get_report
from django.conf import settings
from django.conf.urls.static import static
app_name = 'cases'  # important for namespacing in templates

urlpatterns = [
    path('create/', views.create_case, name='create'),
    path('<int:pk>/', views.case_detail, name='detail'),
    path('<int:pk>/update_status/', views.update_case_status, name='update_status'),
    path('<int:pk>/delete/', views.delete_case, name='delete'),
    path('<int:pk>/report/', views.generate_case_report_pdf, name='report_pdf'),
    path('case/<int:case_id>/report/', get_report, name='get_report'),
    path('status/result/<str:case_id>/report/', views.get_report, name='report_pdf'),
    path('list/', views.public_missing_list, name='public_missing_list'),
    path('status/check/', views.public_status_check_form, name='status_check'),
    path('status/result/<str:complaint_id>/', views.public_status_detail, name='status_detail'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   
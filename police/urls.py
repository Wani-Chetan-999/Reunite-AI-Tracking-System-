from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import dashboard

app_name = 'police'

urlpatterns = [
    path('register/', views.registration_init, name='register_init'),
    path('register/verify/', views.verify_otp, name='verify_otp'),
    path('login/', views.police_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ajax/load-districts/', views.load_districts, name='ajax_load_districts'),
    path('ajax/load-talukas/', views.load_talukas, name='ajax_load_talukas'),
    path('ajax/load-police-stations/', views.load_police_stations, name='ajax_load_police_stations'),
    path('logout/', views.police_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password-otp/', views.forgot_password_otp, name='forgot_password_otp'),
    path('  ', views.reset_password, name='reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/action/', views.handle_notification_action, name='notification_action'), # NEW
    path('surveillance_match/', views.surveillance_match_api, name='surveillance_match'),
] +static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

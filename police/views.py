from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import send_mail
import random, hashlib
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from cases.ai_processor import match_live_face_to_db

from .models import (
    PoliceUser, PoliceProfile, OTPVerification,
    State, District, Taluka, PoliceStation, PoliceAuthList
)
from .forms import PoliceRegistrationInitForm, OTPVerifyForm, PoliceLoginForm
from .forms import ForgotPasswordForm, OTPVerifyForm, ResetPasswordForm

# ---------- AJAX loaders ----------
def load_districts(request):
    state_id = request.GET.get('state')
    districts = District.objects.filter(state_id=state_id).order_by('name')
    return JsonResponse(list(districts.values('id', 'name')), safe=False)

def load_talukas(request):
    district_id = request.GET.get('district')
    talukas = Taluka.objects.filter(district_id=district_id).order_by('name')
    return JsonResponse(list(talukas.values('id', 'name')), safe=False)

def load_police_stations(request):
    taluka_id = request.GET.get('taluka')
    stations = PoliceStation.objects.filter(taluka_id=taluka_id).order_by('name')
    return JsonResponse(list(stations.values('id', 'name', 'email')), safe=False)

# ---------- OTP utilities ----------
def generate_otp():
    return f"{random.randint(100000, 999999)}"

def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

def send_otp_email(email, otp):
    subject = "Reunite Portal — Your verification OTP"
    message = f"Your OTP for registration is: {otp}\nThis code is valid for 10 minutes.\nDo not share it with anyone."
    # use Django send_mail configured in settings
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

# ---------- Registration: init (send OTP) ----------
def registration_init(request):
    if request.method == 'POST':
        form = PoliceRegistrationInitForm(request.POST)
        if form.is_valid():
            station = form.cleaned_data['police_station']  # this is a PoliceStation instance
            # Resolve email from police station
            station_email = station.email or ''
            if not station_email:
                messages.error(request, 'Selected police station has no email configured.')
                return render(request, 'police/register_init.html', {'form': form})

            # Generate & store OTP record
            otp = generate_otp()
            OTPVerification.objects.create(
                email=station_email,
                otp_hash=hash_otp(otp),
                expires_at=timezone.now() + timedelta(minutes=10)
            )

            # Send OTP to station email
            send_otp_email(station_email, otp)

            # Save registration data in session (store station id and station_email instead of raw email field)
            reg_data = {
                'state': form.cleaned_data['state'].id,
                'district': form.cleaned_data['district'].id,
                'taluka': form.cleaned_data['taluka'].id,
                'police_station_id': station.id,
                'officer_name': form.cleaned_data['officer_name'],
                'region_number': form.cleaned_data.get('region_number'),
                'phone_number': form.cleaned_data['phone_number'],
                'police_station_address': form.cleaned_data.get('police_station_address', ''),
                'pincode': form.cleaned_data.get('pincode', ''),
                'password': form.cleaned_data['password'],
                'station_email': station_email,
            }
            request.session['police_reg_data'] = reg_data
            # redirect to OTP verify page
            return redirect('police:verify_otp')
    else:
        form = PoliceRegistrationInitForm()
    return render(request, 'police/register_init.html', {'form': form})

# ---------- Verify OTP and create account ----------
def verify_otp(request):
    reg_data = request.session.get('police_reg_data')
    if not reg_data:
        messages.error(request, 'No registration data found. Start again.')
        return redirect('police:register_init')

    initial = {'email': reg_data.get('station_email')}
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            otp_input = form.cleaned_data['otp']

            otp_entry = OTPVerification.objects.filter(email__iexact=email, is_used=False).order_by('-created_at').first()
            if not otp_entry:
                messages.error(request, 'No OTP found or it has expired. Please request a new OTP.')
                return redirect('police:register_init')

            # expiry and attempt checks
            if timezone.now() > otp_entry.expires_at:
                messages.error(request, 'OTP expired. Request again.')
                return redirect('police:register_init')

            if otp_entry.attempts >= 5:
                messages.error(request, 'Too many invalid attempts. Request a new OTP.')
                return redirect('police:register_init')

            if hash_otp(otp_input) != otp_entry.otp_hash:
                otp_entry.attempts += 1
                otp_entry.save()
                messages.error(request, 'Invalid OTP. Try again.')
                return render(request, 'police/verify_otp.html', {'form': form})

            # OTP valid -> create user & profile
            password = reg_data['password']
            station_id = reg_data['police_station_id']
            station = PoliceStation.objects.get(id=station_id)

            # create user
            user = PoliceUser.objects.create_user(email=email, password=password)

            # create profile
            profile = PoliceProfile.objects.create(
                user=user,
                officer_name=reg_data.get('officer_name'),
                region_number=reg_data.get('region_number'),
                phone_number=reg_data.get('phone_number'),
                state_id=reg_data.get('state'),
                district_id=reg_data.get('district'),
                taluka_id=reg_data.get('taluka'),
                police_station_name=station.name,
                police_station_address=reg_data.get('police_station_address'),
                pincode=reg_data.get('pincode')
            )

            # mark OTP used
            otp_entry.is_used = True
            otp_entry.save()

            # clear session
            try:
                del request.session['police_reg_data']
            except KeyError:
                pass

            messages.success(request, 'Registration complete. You can now log in.')
            return redirect('police:login')
    else:
        form = OTPVerifyForm(initial=initial)

    return render(request, 'police/verify_otp.html', {'form': form})

# ---------- Simple login & dashboard placeholders ----------
def police_login(request):
    if request.method == 'POST':
        form = PoliceLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)  # <-- sets request.user
            messages.success(request, 'Login successful!')
            return redirect('police:dashboard')
    else:
        form = PoliceLoginForm()
    return render(request, 'police/login.html', {'form': form})

from django.shortcuts import render
from cases.models import Case


# views.py (Example dashboard view)
# police/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from cases.models import Case, CasePhoto # Ensure CasePhoto is imported
# Assuming PoliceProfile or equivalent is accessible via request.user.profile
from django.utils import timezone
# Import DetectionAlert model along with the others
from cases.models import Case, CasePhoto, DetectionAlert 
# Assuming PoliceProfile or equivalent is accessible via request.user.profile

@login_required
def dashboard(request):
    # --- 1. Base Case Query (Remains the same) ---
    all_cases = Case.objects.filter(police_officer=request.user).order_by('-created_at')

    total_cases = all_cases.count()
    pending_cases = all_cases.filter(status='pending').count()
    closed_cases = all_cases.filter(status__in=['closed', 'resolved']).count()

    # --- 2. AI NOTIFICATION LOGIC (Using DetectionAlert) ---
    user_profile = request.user.profile 
    last_view_time = user_profile.last_dashboard_view
    
    # Get the IDs of all cases relevant to this officer
    relevant_case_ids = all_cases.values_list('id', flat=True)
    
    # Base Query for Alerts: Only show non-deleted alerts for this officer's cases
    base_alerts_query = DetectionAlert.objects.filter(
        case_id__in=relevant_case_ids,
        is_deleted_by_officer=False 
    )
    
    # A. Fetch ALL Non-Deleted Alerts (Full list for the modal)
    # We select related models to access the case and photo details in the template
    all_alerts_for_officer = base_alerts_query.select_related(
        'case', 
        'detection_photo'
    ).order_by('-alert_sent_at')
    
    # B. Count UNREAD Alerts (Filter by uploaded_at > last_view_time)
    unread_alerts_count = all_alerts_for_officer.filter(
        alert_sent_at__gt=last_view_time
    ).count()

    # --- 3. CLEAR NOTIFICATIONS (Update last view time) ---
    # This marks all current notifications as 'read' for the next visit
    user_profile.last_dashboard_view = timezone.now()
    user_profile.save(update_fields=['last_dashboard_view'])
    
    
    # --- 4. Render Context ---
    return render(request, 'police/dashboard.html', {
        'cases': all_cases,
        'total_cases': total_cases,
        'pending_cases': pending_cases,
        'closed_cases': closed_cases,
        'notifications_count': unread_alerts_count,         # UNREAD count for the KPI tile
        'all_detections_list': all_alerts_for_officer,      # Full list for the modal (filtered by delete status)
    })

from django.views.decorators.http import require_POST # New import
from django.views.decorators.csrf import csrf_exempt # New import
# police/views.py (Inside handle_notification_action)
from cases.models import DetectionAlert
@require_POST
@login_required
@csrf_exempt 
def handle_notification_action(request):
    action = request.POST.get('action') # 'read' or 'delete'
    alert_pk = request.POST.get('alert_pk') # PK of the DetectionAlert
    
    try:
        # Note: We query the DetectionAlert model
        alert = DetectionAlert.objects.get(pk=alert_pk)
        
        if alert.case.police_officer != request.user:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized action.'}, status=403)
        
        if action == 'delete':
            # Soft Delete: Only update the alert status, preserving the CasePhoto evidence
            alert.is_deleted_by_officer = True
            alert.save(update_fields=['is_deleted_by_officer'])
            return JsonResponse({'status': 'success', 'message': 'Notification deleted.'})
            
        elif action == 'read':
            alert.is_reviewed = True
            alert.save(update_fields=['is_reviewed'])
            return JsonResponse({'status': 'success', 'message': 'Notification marked as read.'})

        return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)

    except DetectionAlert.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Alert not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def police_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('police:login')

User = get_user_model()

def generate_otp():
    return f"{random.randint(100000, 999999)}"

def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

def send_otp_email(email, otp):
    send_mail(
        'Your OTP for Password Reset',
        f'Your OTP is {otp}',
        None,
        [email],
        fail_silently=False
    )

# Step 1: Enter Email
def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Email not found")
                return render(request, 'police/forgot_password.html', {'form': form})

            otp = generate_otp()
            OTPVerification.objects.create(
                email=email,
                otp_hash=hash_otp(otp),
                purpose='password_reset',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            send_otp_email(email, otp)
            request.session['password_reset_email'] = email
            messages.success(request, f"OTP sent to {email}")
            return redirect('police:forgot_password_otp')
    else:
        form = ForgotPasswordForm()
    return render(request, 'police/forgot_password.html', {'form': form})

# Step 2: Verify OTP
def forgot_password_otp(request):
    email = request.session.get('password_reset_email')
    if not email:
        return redirect('police:forgot_password')

    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            otp_entries = OTPVerification.objects.filter(email=email, is_used=False, purpose='password_reset').order_by('-created_at')
            if not otp_entries:
                messages.error(request, "No OTP found. Request again.")
                return redirect('police:forgot_password')
            entry = otp_entries[0]

            if timezone.now() > entry.expires_at:
                messages.error(request, "OTP expired. Request again.")
                return redirect('police:forgot_password')

            if entry.attempts >= 5:
                messages.error(request, "Too many attempts. Request new OTP.")
                return redirect('police:forgot_password')

            if hash_otp(otp) != entry.otp_hash:
                entry.attempts += 1
                entry.save()
                messages.error(request, "Invalid OTP. Try again.")
                return render(request, 'police/forgot_password_otp.html', {'form': form})

            entry.is_used = True
            entry.save()
            request.session['password_reset_verified'] = True
            return redirect('police:reset_password')
    else:
        form = OTPVerifyForm(initial={'email': email})
    return render(request, 'police/forgot_password_otp.html', {'form': form})

# Step 3: Reset Password
def reset_password(request):
    email = request.session.get('password_reset_email')
    verified = request.session.get('password_reset_verified')
    if not email or not verified:
        return redirect('police:forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successful. You can now log in.")
            del request.session['password_reset_email']
            del request.session['password_reset_verified']
            return redirect('police:login')
    else:
        form = ResetPasswordForm()
    return render(request, 'police/reset_password.html', {'form': form})


# police/views.py (Add the necessary imports and modify the function)

# ... (Existing imports) ...
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
import base64
import os
import random # Keep random for testing the bounding box logic
from cases.ai_processor import match_live_face_to_db # NEW IMPORT
# police/views.py (The updated function)

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.files.base import ContentFile # For saving files from bytes
import base64
import json
import uuid
import os
import random # Used for testing bounding boxes

from cases.models import Case, CasePhoto # Ensure Case is imported
from cases.ai_processor import match_live_face_to_db # AI Matching Function
# from cases.tasks import send_detection_alert_email
from cases.tasks import send_detection_alert_email
# police/views.py (Final version focused on Evidence Logging)


# police/views.py (Final version integrating DetectionAlert)

# Ensure you have imported the necessary models and tasks:
# from cases.models import Case, CasePhoto, DetectionAlert 
# from cases.tasks import send_detection_alert_email 
# from datetime import timedelta, timezone, etc.

@login_required
@csrf_exempt 
# police/views.py (Final version integrating distinct logging and alert throttling)

@login_required
@csrf_exempt 
def surveillance_match_api(request):
    """
    Receives live image frame via POST, runs AI matching.
    1. Logs CasePhoto evidence for ALL detections (no throttle).
    2. Triggers Alert/Email only once per minute (throttled).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Safely retrieve location data (will be None if permission is denied)
            location_data = data.get('location', {})
            latitude = location_data.get('lat')
            longitude = location_data.get('lon')
            image_b64_full = data.get('image', '')
            
            if not image_b64_full:
                 return JsonResponse({'status': 'error', 'message': 'No image data received.'}, status=400)

            # 1. Decode Image Data
            image_b64_data = image_b64_full.split(',')[1] 
            image_bytes = base64.b64decode(image_b64_data)
            
            # 2. Run Multi-Face AI Matching
            match_results_list = match_live_face_to_db(image_bytes)
            
            if match_results_list:
                
                # Cooldown period for ALERTS (1 Minute)
                cooldown_period_alert = timedelta(minutes=1) 
                
                for match in match_results_list:
                    case_id_str = match['case_id']
                    similarity = match['similarity']
                    
                    # 3. Retrieve the Case object
                    try:
                        case_obj = Case.objects.get(complaint_id=case_id_str) 
                    except Case.DoesNotExist:
                        continue
                        
                    # --- 4. EVIDENCE LOGGING (NO THROTTLE HERE) ---
                    # This runs IMMEDIATELY for every confirmed match.
                    file_name = f"{case_id_str}_Detection_{uuid.uuid4().hex[:6]}.jpg"
                    image_file = ContentFile(image_bytes, name=file_name)
                    
                    new_photo = CasePhoto.objects.create(
                        case=case_obj, 
                        image=image_file,
                        is_detection_evidence=True,
                        latitude=latitude,
                        longitude=longitude 
                    )
                    print(f"EVIDENCE LOGGED: Photo saved for Case {case_id_str}.")
                    
                    # 5. ALERT NOTIFICATION THROTTLING CHECK (Check DetectionAlert model)
                    latest_alert = DetectionAlert.objects.filter(
                        case=case_obj
                    ).order_by('-alert_sent_at').first()

                    if latest_alert and (timezone.now() - latest_alert.alert_sent_at) < cooldown_period_alert:
                        print(f"ALERT SKIPPED: Case {case_id_str} is in 1 min alert cooldown.")
                        # Alert is skipped, but the photo is already saved as evidence (new_photo).
                        continue 

                    # 6. IF COOLDOWN EXPIRED: Create NEW ALERT RECORD & TRIGGER EMAIL
                    
                    # Create the new alert record
                    DetectionAlert.objects.create(
                        case=case_obj,
                        detection_photo=new_photo, # Link to the newly saved evidence photo
                    )

                    # Trigger Celery Email Task (Celery task performs its own 2-min email check)
                    send_detection_alert_email.delay(
                        case_obj.pk,
                        new_photo.pk, 
                        similarity,
                        latitude,
                        longitude 
                    )
                    
                    print(f"ALERT DISPATCHED for Case {case_id_str}. NEW ALERT CREATED.")
                
                # 7. Return the full list of detections to the Frontend for drawing
                response_data = {
                    'status': 'match_found',
                    'detections': match_results_list 
                }
            else:
                response_data = {'status': 'no_match', 'detections': []}
            
            return JsonResponse(response_data)
        
        except Exception as e:
            print(f"Surveillance API Critical Error: {e}") 
            return JsonResponse({'status': 'error', 'message': 'Internal processing error.'}, status=400)
    
    return JsonResponse({'status': 'invalid_method'}, status=405)

# cases/tasks.py

from celery import shared_task
from django.conf import settings
from .models import Case, FaceEmbedding
from .ai_processor import generate_embedding_from_image # Import the AI function
import os
import numpy as np

# This was for to process only one image at a time via Celery.
# @shared_task
# def process_new_case_photo_for_embedding(case_id, image_relative_path):
#     """
#     Celery task to asynchronously generate and save the face embedding for a new case.
#     """
#     try:
#         case = Case.objects.get(pk=case_id)
#     except Case.DoesNotExist:
#         print(f"Celery Error: Case ID {case_id} not found.")
#         return

#     print(f"Celery Task: Starting AI processing for Case ID {case_id} using path: {image_relative_path}")

#     # Call the blocking AI function
#     embedding_list = generate_embedding_from_image(image_relative_path)

#     if embedding_list:
#         # Create the FaceEmbedding record once the vector is ready
#         FaceEmbedding.objects.create(
#             case=case,
#             embedding_vector=embedding_list,
#             source_image_path=image_relative_path
#         )
#         print(f"Celery Task: Successfully saved embedding for Case ID {case_id}.")
#         # Optional: Send a follow-up email/notification that AI processing is complete
#     else:
#         print(f"Celery Task: Failed to generate embedding for Case ID {case_id}. Image quality issue.")



# cases/tasks.py (Modified process_new_case_photo_for_embedding)

@shared_task
def process_new_case_photo_for_embedding(case_id): # Note: Removed image_relative_path argument
    
    try:
        case = Case.objects.get(pk=case_id)
    except Case.DoesNotExist:
        return
    
    # 1. Collect all non-detection photos
    enrollment_photos = case.photos.filter(is_detection_evidence=False)
    
    if not enrollment_photos:
        print(f"Celery Task: No enrollment photos found for Case ID {case_id}.")
        return

    all_vectors = []
    
    # 2. Iterate through all photos and generate vectors
    for photo in enrollment_photos:
        image_path = os.path.join(settings.MEDIA_ROOT, photo.image.name)
        
        # Call the AI function (must be updated to handle multiple calls)
        vector_list = generate_embedding_from_image(image_path) # AI call
        
        if vector_list:
            all_vectors.append(np.array(vector_list))
            print(f"Celery Task: Generated vector for photo {photo.id}.")
        else:
            # Handle failure for a single photo (e.g., face not detected)
            print(f"Celery Task: Failed to generate vector for photo {photo.id}.")


    # 3. Aggregate Vectors (Create the Mean Vector)
    if all_vectors:
        # Stack all vectors into a NumPy array and calculate the mean vector
        mean_vector_np = np.mean(np.stack(all_vectors), axis=0)
        mean_vector_list = mean_vector_np.tolist()

        # 4. Save the Final Mean Vector
        FaceEmbedding.objects.create(
            case=case,
            embedding_vector=mean_vector_list,
            source_image_path=f"Aggregated from {len(all_vectors)} photos." 
        )
        print(f"Celery Task: Successfully saved AGGREGATED embedding for Case ID {case_id}.")
    else:
        print(f"Celery Task: No valid vectors could be generated for Case ID {case_id}.")
        
# cases/tasks.py (Modified send_detection_alert_email function)
# cases/tasks.py (The final, corrected send_detection_alert_email)
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Case 
# Assuming CasePhoto model is also imported/accessible in this module's scope if needed
from .models import Case, CasePhoto, DetectionAlert
from django.conf import settings 
import os
from email.mime.image import MIMEImage


# cases/tasks.py (Final, complete version)
# @shared_task
# def send_detection_alert_email(case_id, detection_photo_pk, similarity, latitude, longitude):
#     # This task now accepts five positional arguments, matching the trigger call.
    
#     try:
#         case = Case.objects.get(pk=case_id)
        
#         # 1. FETCH ALL REQUIRED DATA FROM DB (robust)
#         detection_photo = CasePhoto.objects.get(pk=detection_photo_pk)
        
#         # Extract data from the fetched photo object
#         # NOTE: latitude and longitude are now taken directly from the function arguments
#         # passed from police/views.py, ensuring we use the latest values.
#         detection_photo_path = detection_photo.image.name
        
#         # --- 2. ALERT COOLDOWN CHECK (Throttling) ---
#         now = timezone.now()
#         cooldown_period = timedelta(minutes=2)
        
#         last_alert = DetectionAlert.objects.filter(
#             case=case
#         ).order_by('-alert_sent_at').first()
        
#         if last_alert and (timezone.now() - last_alert.alert_sent_at) < cooldown_period:
#             print(f"ALERT SKIPPED (Email Throttle): Case {case.complaint_id} is in 2 min cooldown.")
#             return
#         detection_photo = CasePhoto.objects.get(pk=detection_photo_pk)
        
#         new_alert = DetectionAlert.objects.create(
#             case=case,
#             detection_photo=detection_photo,
#             # alert_sent_at is auto-set to now()
#         )

#         # 3. Prepare Content & URLs
#         subject = f"🚨 HIGH PRIORITY ALERT: Match Found for Case ID {case.complaint_id}"
#         image_cid = f'detection_image_{case.pk}'
        
#         # --- LOCATION LOGIC ---
#         if latitude and longitude:
#             map_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
#             location_string = f"{latitude}, {longitude}"
#         else:
#             map_link = None
#             location_string = "Location Data Unavailable"
#         # ---------------------

#         # 4. Attach Image (CRITICAL FOR DISPLAY IN GMAIL)
#         photo_abs_path = os.path.join(settings.MEDIA_ROOT, detection_photo_path) 
        
#         email = EmailMultiAlternatives(
#             subject=subject,
#             body=(
#                 f"URGENT: AI detected a match for {case.missing_name} (Case ID: {case.complaint_id}).\n"
#                 f"Confidence: {similarity*100:.2f}% | Location: {location_string}\n"
#                 f"Action Required: Check the case dashboard immediately."
#             ),
#             to=[case.police_officer.email],
#             cc=[case.guardian_email]
#         )
        
#         # Read the file and attach it inline
#         try:
#             with open(photo_abs_path, 'rb') as f:
#                 img = MIMEImage(f.read())
#                 img.add_header('Content-ID', f'<{image_cid}>')
#                 email.attach(img)
#         except FileNotFoundError:
#             print(f"ERROR: Image file not found at {photo_abs_path}. Skipping image attachment.")

#         # 5. Attach HTML Content
#         html_content = render_to_string(
#             'emails/detection_alert.html',
#             {
#                 'case': case,
#                 'image_cid': image_cid, 
#                 'similarity': f"{similarity*100:.2f}%",
#                 'location_link': map_link,
#                 'location_coords': location_string,
#                 'officer_email': case.police_officer.email if case.police_officer else 'N/A'
#             }
#         )
#         email.attach_alternative(html_content, "text/html")
#         email.send()
        
#         print(f"ALERT SENT: Email alert successfully dispatched for Case {case.complaint_id}.")

#         # 6. UPDATE TIMESTAMP
#         case.last_alert_sent = now
#         case.save(update_fields=['last_alert_sent'])
        
#     except Case.DoesNotExist:
#         print(f"Celery Error: Case ID {case_id} not found.")
#     except Exception as e:
#         print(f"Celery Error sending detection email for Case {case_id}: {e}")
        
@shared_task
def send_detection_alert_email(case_id, detection_photo_pk, similarity, latitude, longitude):
    """
    Sends a high-priority email alert upon confirmed AI detection, including location data,
    and throttles alerts to one per 2-minute cooldown period.
    """
    
    try:
        # Fetch the core Case and Photo objects first
        case = Case.objects.get(pk=case_id)
        detection_photo = CasePhoto.objects.get(pk=detection_photo_pk)
        
        # --- 1. ALERT COOLDOWN CHECK (Throttling) ---
        now = timezone.now()
        cooldown_period = timedelta(minutes=2)
        
        # Check the last time an alert was successfully sent for this case
        last_alert = DetectionAlert.objects.filter(
            case=case
        ).order_by('-alert_sent_at').first()
        
        if last_alert and (now - last_alert.alert_sent_at) < cooldown_period:
            print(f"ALERT SKIPPED (Email Throttle): Case {case.complaint_id} is in 2 min cooldown.")
            return

        # 2. CREATE NEW ALERT RECORD (The Notification Log) 
        # This must happen BEFORE the email is sent, as it sets the new 'last_alert_sent' time.
        new_alert = DetectionAlert.objects.create(
            case=case,
            detection_photo=detection_photo,
            # alert_sent_at is auto-set to now()
        )
        
        # --- 3. Prepare Content & URLs ---
        
        detection_photo_path = detection_photo.image.name
        subject = f"🚨 HIGH PRIORITY ALERT: Match Found for Case ID {case.complaint_id}"
        image_cid = f'detection_image_{case.pk}'
        
        # Build Photo URL (used for external viewing/linking, though CID is used for display)
        photo_url = f"{settings.SITE_URL}{settings.MEDIA_URL}{detection_photo_path}"
        
        # Determine location display strings
        if latitude and longitude:
            map_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            location_string = f"{latitude}, {longitude}"
        else:
            map_link = None
            location_string = "Location Data Unavailable"
            
        # 4. Attach Image (CRITICAL FOR DISPLAY IN GMAIL)
        photo_abs_path = os.path.join(settings.MEDIA_ROOT, detection_photo_path) 
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=(
                f"URGENT: AI detected a match for {case.missing_name} (Case ID: {case.complaint_id}).\n"
                f"Confidence: {similarity*100:.2f}% | Location: {location_string}\n"
                f"Action Required: Check the case dashboard immediately."
            ),
            to=[case.police_officer.email],
            cc=[case.guardian_email]
        )
        
        # Read the file and attach it inline
        try:
            with open(photo_abs_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', f'<{image_cid}>')
                email.attach(img)
        except FileNotFoundError:
            print(f"ERROR: Image file not found at {photo_abs_path}. Skipping image attachment.")

        # 5. Attach HTML Content
        html_content = render_to_string(
            'emails/detection_alert.html',
            {
                'case': case,
                'image_cid': image_cid, 
                'similarity': f"{similarity*100:.2f}%",
                'location_link': map_link,
                'location_coords': location_string,
                'officer_email': case.police_officer.email if case.police_officer else 'N/A'
            }
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"ALERT SENT: Email alert successfully dispatched for Case {case.complaint_id}.")

        # 6. UPDATE TIMESTAMP
        # The 'last_alert_sent' field is now obsolete because we are relying on the DetectionAlert model.
        # We can remove the Case model update line entirely for a cleaner separation of concerns.
        
    except Case.DoesNotExist:
        print(f"Celery Error: Case ID {case_id} not found.")
    except Exception as e:
        print(f"Celery Error sending detection email for Case {case_id}: {e}")
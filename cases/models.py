import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils import timezone 

GENDER_CHOICES = [  
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

CASE_TYPE_CHOICES = [
    ('missing', 'Missing Person'),
    ('kidnapping', 'Kidnapping'),
    ('runaway', 'Runaway'),
    ('unknown', 'Unknown'),
]

URGENCY_CHOICES = [
    ('normal', 'Normal'),
    ('high', 'High'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('verified', 'Verified'),
    ('closed', 'Closed'),
]

class Case(models.Model):
    
    class Status(models.TextChoices): # Use TextChoices for Django >= 3.0
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        CLOSED = 'closed', 'Closed'
        
    complaint_id = models.CharField(max_length=20, unique=True, blank=True)

    # Guardian / complainant
    guardian_name = models.CharField(max_length=200,blank=False)
    guardian_relationship = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(blank=True, null=True)
    guardian_address = models.TextField()
    guardian_aadhaar = models.CharField(max_length=12, blank=True, null=True)  # optional

    # Missing person
    missing_name = models.CharField(max_length=200)
    missing_age = models.PositiveIntegerField(blank=True, null=True)
    missing_dob = models.DateField(blank=True, null=True)
    missing_gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    missing_height = models.CharField(max_length=50, blank=True, null=True)
    missing_weight = models.CharField(max_length=50, blank=True, null=True)
    missing_eye_color = models.CharField(max_length=50, blank=True, null=True)
    missing_hair_color = models.CharField(max_length=50, blank=True, null=True)
    clothing_description = models.TextField(blank=True, null=True)
    special_marks = models.TextField(blank=True, null=True)

    # Last seen / incident
    last_seen_location = models.CharField(max_length=255, blank=True, null=True)
    last_seen_date = models.DateField(blank=True, null=True)
    last_seen_time = models.TimeField(blank=True, null=True)

    # Case metadata
    case_type = models.CharField(max_length=20, choices=CASE_TYPE_CHOICES, default='missing')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='normal')
    notes = models.TextField(blank=True, null=True)

    # system fields
    police_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                       null=True, blank=True, related_name='cases')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    last_alert_sent = models.DateTimeField(null=True, blank=True)
    # cases/models.py

    # def save(self, *args, **kwargs):
    #     # 1. Save the object first if it's new, so it gets a primary key (self.pk)
    #     if not self.pk:
    #         # We must use commit=False in the super() call if we are going to modify fields
    #         # and call super().save() again. For simplicity and standard practice, 
    #         # we rely on the database's auto-incrementing field here.
    #         super().save(*args, **kwargs)

    #         # 2. After the first save, self.pk (the auto-incremented ID) is available.
    #         case_pk = self.pk
            
    #         # 3. Format the ID: Prefix + Year + Padded PK
    #         year = timezone.now().strftime('%y') # Use timezone.now() here
            
    #         # Use self.pk (the unique, atomic counter) for the ID number
    #         self.complaint_id = f"MP-{year}-{case_pk:06d}"
            
    #         # 4. Save the object again to update the complaint_id field
    #         # Use update_fields for efficiency to only save the complaint_id
    #         super().save(update_fields=['complaint_id'])
    #         return # Exit after the second save

    #     # If the object already exists (self.pk is not None), just save normally
    #     super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            # 1. First save to get the unique Primary Key (PK)
            super().save(*args, **kwargs)

            # 2. Generate the complaint_id using the new PK
            case_pk = self.pk
            year = timezone.now().strftime('%y')
            self.complaint_id = f"MP-{year}-{case_pk:06d}"

            # 3. Second save to update the complaint_id field
            super().save(update_fields=['complaint_id'])
            return 

        # Normal save for existing objects
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_id} - {self.missing_name} ({self.status})"
    
# class CasePhoto(models.Model):
#     case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='photos')
#     image = models.ImageField(upload_to='case_photos/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Photo for {self.case.complaint_id}"
    
#     @property
#     def absolute_image_url(self):
#         # This will fail outside of a request context; we handle it in the view.
#         return self.image.url

class CasePhoto(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='case_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # NEW FIELD: Differentiates officer-uploaded photos from AI-logged evidence
    is_detection_evidence = models.BooleanField(default=False) 
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta:
        # Orders photos newest first (descending)
        ordering = ['-uploaded_at']
    def __str__(self):
        # Updated string representation for clarity in the Admin
        return f"Photo for {self.case.complaint_id} (Detection: {self.is_detection_evidence})"
    
    # You can remove the @property absolute_image_url as it's not strictly necessary 
    # since you're using {{ photo.image.url }} directly in the templates.
    
    
# models.py (Add this new model)
from django.db.models.fields.json import JSONField # Use this for PostgreSQL/modern Djangos
# If using older Django/SQLite, you might need a TextField and custom serialization

class FaceEmbedding(models.Model):
    """Stores the unique vector (embedding) of a missing person's face."""
    
    # Links directly to the Case model you provided previously
    case = models.OneToOneField('Case', on_delete=models.CASCADE, related_name='face_embedding')
    
    # Store the vector as a JSON array (list of floats). 
    # ArcFace typically uses 128D or 512D.
    # We use JSONField as it's the standard way to store arrays in modern Django/PostgreSQL.
    embedding_vector = JSONField() 
    
    # Store the path to the original source image that generated this embedding
    source_image_path = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Embedding for Case: {self.case.complaint_id}"
    
class DetectionAlert(models.Model):
    """Logs every instance an email/alert was sent for a case, allowing deletion and throttling."""
    
    case = models.ForeignKey('Case', on_delete=models.CASCADE, related_name='alerts')
    # Link to the evidence photo (optional, but good for context)
    detection_photo = models.ForeignKey('CasePhoto', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Alert state and time
    alert_sent_at = models.DateTimeField(default=timezone.now)
    is_deleted_by_officer = models.BooleanField(default=False)
    
    # We will use this field to check if the notification has been viewed in the modal:
    is_reviewed = models.BooleanField(default=False) 
    
    def __str__(self):
        return f"Alert for Case {self.case.complaint_id} at {self.alert_sent_at.strftime('%H:%M')}"

from django import forms
from .models import Case, CasePhoto
import re
from django.core.exceptions import ValidationError

class CaseForm(forms.ModelForm):
    # Define fields that are MANDATORY for client-side step validation.
    # We include fields that are essential for the workflow, even if they have
    # blank=True in the model (like last_seen_date/location).
    
    # Step 1: Guardian
    MANDATORY_STEP_1 = ['guardian_name', 'guardian_relationship', 'guardian_phone', 'guardian_address']

    # Step 2: Missing Person
    # 'missing_name' is mandatory. Others are blank=True in the model, but you can force them if needed.
    MANDATORY_STEP_2 = ['missing_name','missing_gender'] 
    
    # Step 3: Last Seen (Essential for the case, forcing required)
    MANDATORY_STEP_3 = ['last_seen_location', 'last_seen_date']

    # Step 4: Case Details (Mandatory choices)
    MANDATORY_STEP_4 = ['case_type', 'urgency'] 
    

    class Meta:
        model = Case
        fields = '__all__'
        exclude = (
            'complaint_id', 
            'police_officer', 
            'status', 
            'created_at', 
            'updated_at'
        )
        widgets = {
            # Guardian Info
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'guardian_aadhaar': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style':'resize:none;'}),

            # Missing Person
            'missing_name': forms.TextInput(attrs={'class': 'form-control'}),
            'missing_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'missing_dob': forms.DateInput(attrs={'class': 'form-control', 'type':'date'}),
            'missing_gender': forms.Select(attrs={'class': 'form-select'}),
            'missing_height': forms.TextInput(attrs={'class': 'form-control'}),
            'missing_weight': forms.TextInput(attrs={'class': 'form-control'}),
            'missing_eye_color': forms.TextInput(attrs={'class': 'form-control'}),
            'missing_hair_color': forms.TextInput(attrs={'class': 'form-control'}),
            'clothing_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style':'resize:none;'}),
            'special_marks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style':'resize:none;'}),

            # Last Seen / Incident
            'last_seen_location': forms.TextInput(attrs={'class': 'form-control'}),
            'last_seen_date': forms.DateInput(attrs={'class': 'form-control', 'type':'date'}),
            'last_seen_time': forms.TimeInput(attrs={'class': 'form-control', 'type':'time'}),

            # Case Details
            'case_type': forms.Select(attrs={'class': 'form-select'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style':'resize:none;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Combine all mandatory fields lists
        all_mandatory_fields = (
            self.MANDATORY_STEP_1 + 
            self.MANDATORY_STEP_2 + 
            self.MANDATORY_STEP_3 + 
            self.MANDATORY_STEP_4
        )
        
        # Explicitly set the 'required' HTML attribute for all mandatory fields
        for field_name in all_mandatory_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required'

    def clean_guardian_aadhaar(self):
        a = self.cleaned_data.get('guardian_aadhaar')
        if a:
            # Server-side validation for Aadhaar format
            if not re.fullmatch(r'\d{12}', a):
                raise ValidationError("Aadhaar must be 12 digits.")
        return a


class CasePhotoForm(forms.ModelForm):
    class Meta:
        model = CasePhoto
        fields = ['image']
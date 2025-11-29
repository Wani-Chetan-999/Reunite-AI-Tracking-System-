from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .forms import CaseForm, CasePhotoForm
from django.core.mail import EmailMultiAlternatives
from .models import CasePhoto, Case, FaceEmbedding # Import FaceEmbedding
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os
from django.conf import settings
# Import the AI logic (adjust path if ai_processor.py is elsewhere)
# NOTE: For production, use Celery and import the task handler instead!
from .ai_processor import generate_embedding_from_image 

from .models import CasePhoto, Case, FaceEmbedding 
from .tasks import process_new_case_photo_for_embedding # New: Import the task
# Note: You no longer need 'from .ai_processor import generate_embedding_from_image' here!
# ... (rest of imports) ...

# Create your views here.
def upload_case_photo(request):
    if request.method == 'POST':
        form = CasePhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success-page')
    else:
        form = CasePhotoForm()
    return render(request, 'upload_photo.html', {'form': form})

# cases/views.py (FULL CONTENT - Focus on create_case function)



# ... (other views above here, like upload_case_photo) ...


# cases/views.py (Focus on create_case function)



@login_required
def create_case(request):

    if request.method == 'POST':
        case_form = CaseForm(request.POST)
        files = request.FILES.getlist('images')
        
        if case_form.is_valid():
            case = case_form.save(commit=False)
            case.police_officer = request.user
            case.save()

            has_enrollment_photos = False

            # Save uploaded images
            for f in files:
                # We assume all photos uploaded during case creation are for enrollment/embedding
                photo = CasePhoto.objects.create(case=case, image=f, is_detection_evidence=False)
                has_enrollment_photos = True


            # =========================================================
            # ✨ AI INTEGRATION START: Call Celery Task (Non-Blocking)
            # =========================================================
            if has_enrollment_photos:
                # CORRECT CALL: Pass only the case.id. The task will look up ALL photos.
                # 
                process_new_case_photo_for_embedding.delay(case.id) 
                messages.info(request, "Case registered. AI processing of all photos has started in the background.")
            else:
                messages.warning(request, "No photos uploaded. Cannot initiate AI embedding generation.")
            # =========================================================
            # ✨ AI INTEGRATION END
            # =========================================================


            try:
                # Render HTML content
                html_content = render_to_string(
                    'emails/complaint_confirmation.html',
                    {'case': case}
                )

                # Text fallback version (optional but recommended)
                text_content = f"""
                Complaint Registered Successfully!
                Complaint ID: {case.complaint_id}
                Missing Person: {case.missing_name}
                Status: {case.status}
                """

                # Create email
                email = EmailMultiAlternatives(
                    subject=f"✅ Case Registered - ID: {case.complaint_id}",
                    body=text_content,
                    to=[case.guardian_email]
                )
                email.attach_alternative(html_content, "text/html") 
                email.send()

            except Exception as e:
                print(f"Error sending email: {e}")
                messages.warning(request, "Case registered but confirmation email failed.")


            messages.success(request, "Case registered successfully.")
            return redirect(
                f"{redirect('police:dashboard').url}?success=true&id={case.complaint_id}"
            )
    else:
        case_form = CaseForm()

    return render(request, 'cases/create_case.html', {
        'case_form': case_form,
    })


# last Code snippet commented out    
# @login_required
# def create_case(request):

#     if request.method == 'POST':
#         case_form = CaseForm(request.POST)
#         files = request.FILES.getlist('images')  # note: template must use name="images"
#         if case_form.is_valid():
#             case = case_form.save(commit=False)
#             case.police_officer = request.user
#             case.save()

#             # save uploaded images (if any)
#             for f in files:
#                 CasePhoto.objects.create(case=case, image=f)

#             try:
#                 # Render HTML content
#                 html_content = render_to_string(
#                     'emails/complaint_confirmation.html',
#                     {'case': case}
#                 )

#                 # Text fallback version (optional but recommended)
#                 text_content = f"""
#                 Complaint Registered Successfully!
#                 Complaint ID: {case.complaint_id}
#                 Missing Person: {case.missing_name}
#                 Status: {case.status}
#                 """

#                 # Create email
#                 email = EmailMultiAlternatives(
#                     subject=f"✅ Case Registered - ID: {case.complaint_id}",
#                     body=text_content,
#                     to=[case.guardian_email]
#                 )
#                 email.attach_alternative(html_content, "text/html")  # Attach HTML version
#                 email.send()

#             except Exception as e:
#                 print(f"Error sending email: {e}")
#                 messages.warning(request, "Case registered but confirmation email failed.")


#             messages.success(request, "Case registered successfully.")  
#             return redirect(
#                 f"{redirect('police:dashboard').url}?success=true&id={case.complaint_id}"
#             )
#     else:
#         case_form = CaseForm()

#     return render(request, 'cases/create_case.html', {
#         'case_form': case_form,
#     })


from django.shortcuts import render, get_object_or_404
from .models import Case
@login_required
def case_detail(request, pk):
    """
    Displays the detailed information for a specific missing person case.
    """
    case = get_object_or_404(Case, pk=pk)
    
    # You can add logic here to check if the user is authorized to view the case.

    return render(request, 'cases/case_detail.html', {'case': case})

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
# You'll need a simple form for status update, e.g., CaseStatusForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Case # Make sure Case is imported

@login_required
def update_case_status(request, pk):
    case = get_object_or_404(Case, pk=pk)
    
    valid_statuses = [choice[0] for choice in Case._meta.get_field('status').choices]

    if request.method == 'POST':
        new_status = request.POST.get('status') 
        
        if new_status and new_status in valid_statuses:
            case.status = new_status
            case.save()
            messages.success(request, f"Case status updated to {new_status.upper()}.")
        else:
            messages.error(request, "Invalid status provided or status field missing.")

    return redirect('cases:detail', pk=case.pk)


@login_required
def delete_case(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        case.delete()
        messages.success(request, f"Case {case.complaint_id} successfully deleted.")
        return redirect('police:dashboard') # Redirect after deletion

    # If accessed via GET (shouldn't happen with the form), redirect back
    return redirect('cases:detail', pk=case.pk)

# cases/views.py (within the imports section)
# Make sure you have these imports for ReportLab
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.utils import timezone # Make sure timezone is imported


@login_required
def generate_case_report_pdf(request, pk):
    """Generates a PDF report for a single case using ReportLab."""
    case = get_object_or_404(Case, pk=pk)

    # 1. Setup the HTTP Response and PDF Document
    response = HttpResponse(content_type='application/pdf')
    filename = f'Case_Report_{case.complaint_id}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response, pagesize=A4, 
                            leftMargin=0.8*inch, rightMargin=0.8*inch, 
                            topMargin=0.8*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    story = []

    # --- Custom Styles ---
    primary_color = colors.HexColor('#0b4187')
    styles.add(ParagraphStyle('HeadingTitle', parent=styles['Title'], fontSize=18, textColor=primary_color, spaceAfter=6))
    styles.add(ParagraphStyle('SectionHeader', parent=styles['h3'], fontSize=14, textColor=primary_color, spaceBefore=18, spaceAfter=6))
    styles.add(ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold', textColor=colors.black))
    
    # # Safely get the officer name
    # officer = case.police_officer
    # officer_name = f'{officer.first_name} {officer.last_name}'.strip() if officer and officer.first_name else "[Officer Name Not Set]"
    
    
    # --- HEADER ---
    story.append(Paragraph(f'REUNITE Missing Persons Bureau', styles['HeadingTitle']))
    story.append(Paragraph(f'Official Case Report | CASE ID: <b>{case.complaint_id}</b>', styles['h2']))
    story.append(Spacer(1, 0.2 * inch))
    
    
    # --- 1. MISSING PERSON DETAILS ---
    story.append(Paragraph('1. Missing Person Details', styles['SectionHeader']))

    missing_person_data = [
        [Paragraph('Name:', styles['Label']), Paragraph(case.missing_name or 'N/A', styles['Normal']),
         Paragraph('Gender:', styles['Label']), Paragraph(case.get_missing_gender_display() or 'N/A', styles['Normal'])],
         
        [Paragraph('Age / DOB:', styles['Label']), Paragraph(f'{case.missing_age or "N/A"} / {case.missing_dob.strftime("%Y-%m-%d") if case.missing_dob else "N/A"}', styles['Normal']),
         Paragraph('Height / Weight:', styles['Label']), Paragraph(f'{case.missing_height or "N/A"} / {case.missing_weight or "N/A"}', styles['Normal'])],

        [Paragraph('Hair/Eye Color:', styles['Label']), Paragraph(f'{case.missing_hair_color or "N/A"} / {case.missing_eye_color or "N/A"}', styles['Normal']),
         Paragraph('Urgency:', styles['Label']), Paragraph(case.urgency.upper(), ParagraphStyle('Urgency', parent=styles['Normal'], textColor=colors.red))],
         
        [Paragraph('Special Marks:', styles['Label']), Paragraph(case.special_marks or 'None', styles['Normal']),
         Paragraph('Clothing:', styles['Label']), Paragraph(case.clothing_description or 'Not specified.', styles['Normal'])]
    ]

    table = Table(missing_person_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    
    # --- 2. INCIDENT & GUARDIAN DETAILS ---
    story.append(Paragraph('2. Incident & Complainant Details', styles['SectionHeader']))

    incident_guardian_data = [
        [Paragraph('Last Seen Location:', styles['Label']), Paragraph(case.last_seen_location or 'Unknown', styles['Normal']),
         Paragraph('Guardian Name:', styles['Label']), Paragraph(case.guardian_name, styles['Normal'])],
         
        [Paragraph('Last Seen Date/Time:', styles['Label']), Paragraph(f'{case.last_seen_date.strftime("%Y-%m-%d") if case.last_seen_date else "N/A"} at {case.last_seen_time or "N/A"}', styles['Normal']),
         Paragraph('Relationship:', styles['Label']), Paragraph(case.guardian_relationship, styles['Normal'])],
         
        [Paragraph('Registration Date:', styles['Label']), Paragraph(case.created_at.strftime("%Y-%m-%d %H:%M"), styles['Normal']),
         Paragraph('Guardian Phone:', styles['Label']), Paragraph(case.guardian_phone, styles['Normal'])],
         
        [Paragraph('Case Type:', styles['Label']), Paragraph(case.case_type.upper(), styles['Normal']),
         Paragraph('Guardian Email:', styles['Label']), Paragraph(case.guardian_email or 'N/A', styles['Normal'])],
         
        [Paragraph('Current Status:', styles['Label']), Paragraph(case.status.upper(), ParagraphStyle('Status', parent=styles['Normal'], textColor=colors.red)),
         Paragraph('Guardian Aadhaar:', styles['Label']), Paragraph(case.guardian_aadhaar or 'N/A', styles['Normal'])],
    ]

    table = Table(incident_guardian_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    
    # --- 3. OFFICER NOTES ---
    story.append(Paragraph('3. Officer Notes', styles['SectionHeader']))
    story.append(Paragraph(case.notes or 'No detailed notes recorded.', styles['Normal']))
    story.append(Spacer(1, 0.5 * inch))


    # --- 4. SIGNATURES AND STAMP ---
    # Simplified signature and officer details block
    signature_data = [
        [Paragraph('______________________________', styles['Normal']), Paragraph('______________________________', styles['Normal'])],
        [Paragraph(f'Officer: A.B.C', styles['Label']), Paragraph(f'Report Generated On: {timezone.now().strftime("%Y-%m-%d %H:%M")}', styles['Label'])],
        [Paragraph(f'Department: Reunite Bureau', styles['Label']), Paragraph('Official Stamp Area', styles['Label'])]
    ]

    table = Table(signature_data, colWidths=[4*inch, 3*inch])
    table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (0,0), 1, colors.black),
        ('LINEBELOW', (1,0), (1,0), 1, colors.black),
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(table)

    # --- Build the PDF ---
    doc.build(story)
    return response


import pdfkit
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Case

path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

def get_report(request, case_id):
    case = get_object_or_404(Case, pk=case_id)

    # Attach fully qualified URLs to images
    for photo in case.photos.all():
        photo.absolute_url = request.build_absolute_uri(photo.image.url)

    base_url = request.build_absolute_uri('/')

    html_string = render_to_string('pdf/case_report.html', {
        'case': case,
        'now': timezone.now(),
        'base_url': base_url
    })

    options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        'enable-local-file-access': "",
        'images': "",
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
        'quiet': ''
    }

    pdf = pdfkit.from_string(html_string, False, configuration=config, options=options)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="case_{case.complaint_id}.pdf"'
    return response
# cases/views.py

from django.shortcuts import render
from .models import Case

def public_missing_list(request):
    # Retrieve cases with 'pending' (newly registered) OR 'verified' (police-reviewed) status.
    # Exclude 'closed' cases.
    active_statuses = ['pending', 'verified'] 
    
    active_cases = Case.objects.filter(
        status__in=active_statuses
    ).order_by('-last_seen_date') 

    context = {
        'cases': active_cases,
        'title': 'Active Missing Persons',
    }
    return render(request, 'cases/missing_persons_list.html', context)

# cases/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms
from .models import Case
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponse

# --- FORM DEFINITION ---
# Simple non-ModelForm for ID input
class ComplaintIDForm(forms.Form):
    complaint_id = forms.CharField(
        max_length=20, 
        label="Enter Complaint ID", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Example: MP-25-000010'})
    )

def public_status_check_form(request):
    if request.method == 'POST':
        form = ComplaintIDForm(request.POST)
        if form.is_valid():
            complaint_id = form.cleaned_data['complaint_id'].upper()
            
            # Redirect to the result page using the entered ID
            return redirect('cases:status_detail', complaint_id=complaint_id)
    else:
        form = ComplaintIDForm()
        
    return render(request, 'public/status_check_form.html', {'form': form})


# cases/views.py

def public_status_detail(request, complaint_id):
    try:
        case = Case.objects.get(complaint_id=complaint_id)
        
        # We only show non-closed cases for public engagement
        if case.status == 'closed':
            # Option 1: Show minimal 'Closed' status
            messages.info(request, f"Case {complaint_id} is currently marked as CLOSED. Please contact police for details.")
            return render(request, 'public/status_detail.html', {'case': case, 'is_sensitive_data': False})
            
        # Placeholder for system/officer updates (You would need an actual CaseUpdate model)
        updates = [
            {'date': case.created_at, 'text': 'Case registered and sent for verification.'},
            {'date': timezone.now(), 'text': 'AI engine initiated real-time scanning across public feeds.'}
        ]
        
        context = {
            'case': case,
            'updates': updates,
            # We explicitly prevent sensitive data like guardian contacts from reaching the template
            'is_sensitive_data': False 
        }
        return render(request, 'public/status_detail.html', context)
        
    except ObjectDoesNotExist:
        messages.error(request, f"Complaint ID '{complaint_id}' not found. Please check the ID.")
        return redirect('public:status_check')
    

    

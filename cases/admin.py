# cases/admin.py

from django.contrib import admin
from .models import Case, CasePhoto # Crucial: Ensure Case and CasePhoto are imported

# Define the Inline for CasePhoto
class CasePhotoInline(admin.TabularInline):
    model = CasePhoto
    extra = 1
    fields = ('image', 'uploaded_at',)
    readonly_fields = ('uploaded_at',)

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    # E108 FIX: These names MUST match the model attributes exactly.
    list_display = (
        'complaint_id',
        'missing_name',
        'guardian_name',
        'status',
        'police_officer',
        'created_at'
    )
    
    #  E116 FIX: These fields must exist on the Case model.
    list_filter = ('status', 'urgency', 'created_at')
    
    search_fields = ('complaint_id', 'missing_name', 'guardian_name', 'guardian_phone')
    
    # E127 FIX: This field must exist on the Case model and be a DateTimeField or DateField.
    date_hierarchy = 'created_at'
    
    inlines = [CasePhotoInline]

@admin.register(CasePhoto)
class CasePhotoAdmin(admin.ModelAdmin):
    list_display = ('case', 'uploaded_at')
    
    
from django.contrib import admin
from .models import FaceEmbedding

@admin.register(FaceEmbedding)
class FaceEmbeddingAdmin(admin.ModelAdmin):
    list_display = ("case", "created_at")
    search_fields = ("case__complaint_id",)
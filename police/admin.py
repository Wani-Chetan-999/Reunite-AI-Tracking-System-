from django.contrib import admin

# Register your models here.
# admin.py (Inside your police or core app)

from django.contrib import admin
from .models import State, District, Taluka, PoliceStation, PoliceAuthList
from django.db import models

# --- 1. Inline Classes for Cascading Data Entry ---

class DistrictInline(admin.TabularInline):
    model = District
    extra = 1

class TalukaInline(admin.TabularInline):
    model = Taluka
    extra = 1

class PoliceStationInline(admin.TabularInline):
    model = PoliceStation
    extra = 1
    # Display fields to make the inline form useful
    fields = ('name', 'email')
    
# --- 2. Main Admin Classes ---

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [DistrictInline] # Allows adding Districts directly

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'state',)
    list_filter = ('state',)
    search_fields = ('name',)
    inlines = [TalukaInline] # Allows adding Talukas directly

@admin.register(Taluka)
class TalukaAdmin(admin.ModelAdmin):
    list_display = ('name', 'district',)
    list_filter = ('district__state', 'district',)
    search_fields = ('name',)
    inlines = [PoliceStationInline] # Allows adding Police Stations directly

@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'taluka', 'email')
    list_filter = ('taluka__district__state', 'taluka__district',)
    search_fields = ('name', 'email',)

# @admin.register(PoliceAuthList)
# class PoliceAuthListAdmin(admin.ModelAdmin):
#     list_display = ('email', 'station_code', 'notes')
#     search_fields = ('email', 'station_code')

# admin.py (Add this to your existing admin registration file)

from django.contrib import admin
from .models import PoliceProfile # Ensure PoliceProfile is imported
# Assuming State, District, Taluka, PoliceUser/User are also imported

@admin.register(PoliceProfile)
class PoliceProfileAdmin(admin.ModelAdmin):
    list_display = (
        'officer_name', 
        'user_email', 
        'phone_number', 
        'police_station_name',
        'last_dashboard_view',
    )
    search_fields = ('officer_name', 'phone_number', 'police_station_name', 'user__email')
    list_filter = ('state', 'district', 'taluka')
    
    # Organize the fields on the edit page using fieldsets
    fieldsets = (
        ('Officer Identity', {
            'fields': (
                'user', 'officer_name', 'region_number', 'phone_number',
            ),
        }),
        ('Assigned Station Location', {
            'fields': (
                ('state', 'district', 'taluka'),
                'police_station_name',
                'police_station_address',
                'pincode',
                ('latitude', 'longitude'), # Group lat/lon side-by-side
            ),
            'classes': ('wide',),
        }),
        ('System Tracking', {
            'fields': ('last_dashboard_view', 'created_at'),
            'classes': ('collapse',), # Makes this section collapsible
        })
    )
    
    # Read-only fields for tracking/system data
    readonly_fields = ('user', 'created_at', 'last_dashboard_view')
    
    # Helper method to display the related User's email
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
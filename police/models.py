from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django import forms
from django.utils import timezone

class PoliceUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class PoliceUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = PoliceUserManager()

    def __str__(self):
        return self.email

class State(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.state.name})"

class Taluka(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='talukas')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.district.name})"



class PoliceAuthList(models.Model):
    # Pre-approved Gmail addresses
    email = models.EmailField(unique=True)
    station_code = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email

class PoliceStation(models.Model):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE, related_name='police_stations')
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200, blank=True, null=True) 

    def __str__(self):
        return f"{self.name} ({self.taluka.name})"
    
class PoliceProfile(models.Model):
    user = models.OneToOneField(PoliceUser, on_delete=models.CASCADE, related_name='profile')
    officer_name = models.CharField(max_length=200)
    region_number = models.CharField(max_length=100, blank=True, null=True) 
    phone_number = models.CharField(max_length=20)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    taluka = models.ForeignKey(Taluka, on_delete=models.SET_NULL, null=True)
    police_station_name = models.CharField(max_length=200)
    police_station_address = models.TextField()
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_dashboard_view = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.officer_name} - {self.police_station_name}"


class OTPVerification(models.Model):
    email = models.EmailField()
    otp_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=50, default='registration')
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.email} (used={self.is_used})"

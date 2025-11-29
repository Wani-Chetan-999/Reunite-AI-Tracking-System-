from django import forms
from .models import State, District, Taluka, PoliceStation
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate


class PoliceLoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password")
            cleaned_data['user'] = user
        return cleaned_data

class PoliceRegistrationInitForm(forms.Form):   
    state = forms.ModelChoiceField(queryset=State.objects.all(), required=True)
    district = forms.ModelChoiceField(queryset=District.objects.none(), required=True)
    taluka = forms.ModelChoiceField(queryset=Taluka.objects.none(), required=True)
    police_station = forms.ModelChoiceField(queryset=PoliceStation.objects.none(), required=True)
    officer_name = forms.CharField(max_length=200)
    region_number = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=20)
    police_station_address = forms.CharField(widget=forms.Textarea)
    pincode = forms.CharField(max_length=10)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically set Districts if State is selected
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['district'].queryset = District.objects.filter(state_id=state_id)
            except:
                pass

        # Dynamically set Talukas if District is selected
        if 'district' in self.data:
            try:
                district_id = int(self.data.get('district'))
                self.fields['taluka'].queryset = Taluka.objects.filter(district_id=district_id)
            except:
                pass

        # Dynamically set Police Stations if Taluka is selected
        if 'taluka' in self.data:
            try:
                taluka_id = int(self.data.get('taluka'))
                self.fields['police_station'].queryset = PoliceStation.objects.filter(taluka_id=taluka_id)
            except:
                pass

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'readonly': 'readonly'}))
    otp = forms.CharField(max_length=10)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Registered Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))

class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    otp = forms.CharField(label="OTP", max_length=6, widget=forms.NumberInput(attrs={'class':'form-control'}))

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={'class':'form-control'}))
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={'class':'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")

        validate_password(p1)
        return cleaned_data

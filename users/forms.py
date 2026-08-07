from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError
import re

class SignupForm(forms.Form):

    first_name = forms.CharField(max_length=30,required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name','class': 'form-control'}))
    last_name = forms.CharField(max_length=30,required=True,widget=forms.TextInput(attrs={'placeholder': 'Last Name','class': 'form-control'}))
    email = forms.EmailField(required=True,widget=forms.EmailInput(attrs={'placeholder': 'Email Address','class': 'form-control'}))
    password1 = forms.CharField(label='New Password',widget=forms.PasswordInput(attrs={'placeholder': 'Enter New Password','class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password',widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class': 'form-control'}))
    phone = forms.CharField(max_length=15,required=True,widget=forms.TextInput(attrs={'placeholder': 'Phone Number','class': 'form-control'}))
    city = forms.CharField(max_length=100,required=True,widget=forms.TextInput(attrs={'placeholder': 'City','class': 'form-control'}))
    country = forms.CharField( max_length=100,required=True,widget=forms.TextInput(attrs={'placeholder': 'Country','class': 'form-control'}))
    address = forms.CharField(max_length=500, required=True,widget=forms.Textarea(attrs={'placeholder': 'Enter your full address','class': 'form-control','rows': 3}))

    class Meta:
        model = User
        fields = ['first_name','last_name','email','password1','password2','phone','city','country','address']

#form field validations
    #firstname validation
    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name").strip()

        if not re.match(r'^[A-Za-z ]+$', first_name):
            raise ValidationError("First name can contain only letters and spaces.")

        return first_name
    
     #lastname validation
    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name").strip()

        if not re.match(r'^[A-Za-z ]+$', last_name):
            raise ValidationError("Last name can contain only letters and spaces.")

        return last_name
    
    #password validation
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Password must contain at least one uppercase letter.")

        if not re.search(r'[a-z]', password1):
            raise ValidationError("Password must contain at least one lowercase letter.")

        if not re.search(r'[0-9]', password1):
            raise ValidationError("Password must contain at least one number.")

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password1):
            raise ValidationError("Password must contain at least one special character.")

        return password1

     #email validation
    def clean_email(self):
        email = self.cleaned_data.get("email").strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email is already registered.")

        return email

     #Phone number validation
    def clean_phone(self):
        phone = re.sub(r"\D", "", self.cleaned_data.get("phone"))

        if not phone.isdigit():
            raise ValidationError("Phone number should contain only digits.")

        if len(phone) != 10:
            raise ValidationError("Phone number must contain exactly 10 digits.")

        if UserProfile.objects.filter(phone=phone).exists():
            raise ValidationError("This mobile number is already registered.")

        return phone

    # City validation
    def clean_city(self):
        city = self.cleaned_data.get("city").strip()

        if not re.match(r'^[A-Za-z ]+$', city):
            raise ValidationError("City can contain only letters and spaces.")

        if len(city) < 2:
            raise ValidationError("City name must be at least 2 characters long.")

        return city

    # Country validation
    def clean_country(self):
        country = self.cleaned_data.get("country").strip()

        if not re.match(r'^[A-Za-z ]+$', country):
            raise ValidationError("Country can contain only letters and spaces.")

        if len(country) < 2:
            raise ValidationError("Country name must be at least 2 characters long.")

        return country

    # Address validation
    def clean_address(self):
        address = self.cleaned_data.get("address").strip()

        if len(address) < 10:
            raise ValidationError("Address must be at least 10 characters long.")

        if len(address) > 500:
            raise ValidationError("Address cannot exceed 500 characters.")

        return address



class OTPVerificationForm(forms.Form):
    otp = forms.CharField(label="OTP",max_length=6,min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter 6-digit OTP",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
            }
        ),
    )

    def clean_otp(self):
        otp = self.cleaned_data["otp"].strip()
        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain only digits.")
        if len(otp) != 6:
            raise forms.ValidationError("OTP must be exactly 6 digits.")
        return otp


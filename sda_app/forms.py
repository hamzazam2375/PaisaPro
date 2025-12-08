from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Account, OTPVerification


class SignUpForm(UserCreationForm):
    """Custom signup form extending Django's UserCreationForm"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # User will be activated after OTP verification
        
        if commit:
            user.save()
            # Create an Account instance for the new user
            Account.objects.create(user=user)
        
        return user


class OTPVerificationForm(forms.Form):
    """Form for OTP verification"""
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': 'Enter 6-digit code',
            'style': 'font-size: 24px; letter-spacing: 5px;',
            'maxlength': '6'
        }),
        help_text='Enter the 6-digit code sent to your email'
    )
    
    def __init__(self, *args, **kwargs):
        self.email = kwargs.pop('email', None)
        super().__init__(*args, **kwargs)
    
    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        
        if not otp_code.isdigit():
            raise forms.ValidationError("OTP code must contain only numbers.")
        
        if self.email:
            try:
                otp_obj = OTPVerification.objects.filter(
                    email=self.email,
                    is_verified=False
                ).latest('created_at')
                
                is_valid, message = otp_obj.verify(otp_code)
                if not is_valid:
                    raise forms.ValidationError(message)
                    
            except OTPVerification.DoesNotExist:
                raise forms.ValidationError("No valid OTP found for this email.")
        
        return otp_code


class ResendOTPForm(forms.Form):
    """Form for resending OTP"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'readonly': True
        })
    )
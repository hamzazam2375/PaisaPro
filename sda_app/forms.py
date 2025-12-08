from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Account, OTPVerification, OtherExpenses


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
        user.is_active = True  # Users are now active by default
        
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


class MonthlyIncomeForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['monthly_income']
        widgets = {
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = OtherExpenses
        fields = ['amount', 'category', 'description', 'expense_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.user and hasattr(self.user, 'account'):
            if amount > self.user.account.current_balance:
                raise forms.ValidationError(f"Expense amount (${amount}) cannot be greater than current balance (${self.user.account.current_balance})")
        return amount


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'})
        }


class EmailChangeStartForm(forms.Form):
    new_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))


class EmailChangeVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}))
    otp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control text-center', 'maxlength': '6'})
    )


class AddSavingsForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )
    add_all = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        add_all = self.cleaned_data.get('add_all', False)
        
        if self.user and hasattr(self.user, 'account'):
            if add_all:
                # If add_all is checked, amount will be set to current balance in view
                return amount
            elif amount > self.user.account.current_balance:
                raise forms.ValidationError(f"Amount (${amount}) cannot be greater than current balance (${self.user.account.current_balance})")
        return amount


class WithdrawSavingsForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.user and hasattr(self.user, 'account'):
            if amount > self.user.account.savings:
                raise forms.ValidationError(f"Withdrawal amount (${amount}) cannot be greater than available savings (${self.user.account.savings})")
        return amount


class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )
    money_type = forms.ChoiceField(
        choices=[
            ('salary', 'Salary'),
            ('investment', 'Investment'),
            ('bonus', 'Bonus'),
            ('other', 'Other Income'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional description'})
    )
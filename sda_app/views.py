from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .forms import SignUpForm, OTPVerificationForm, ResendOTPForm
from .models import User, OTPVerification
from .email_service import OTPService


def signup_view(request):
    """Handle user signup with email verification"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Check if email is verified
            email = form.cleaned_data['email']
            try:
                otp_obj = OTPVerification.objects.filter(email=email, is_verified=True).latest('created_at')
                if otp_obj.is_verified:
                    user = form.save()
                    # Create an Account instance for the new user (only if it doesn't exist)
                    from .models import Account
                    if not hasattr(user, 'account'):
                        Account.objects.create(user=user)
                    
                    # Login the user
                    login(request, user)
                    messages.success(request, 'Account created successfully! Welcome to PaisaPro!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Please verify your email first.')
            except OTPVerification.DoesNotExist:
                messages.error(request, 'Please verify your email first.')
    else:
        form = SignUpForm()
    
    return render(request, 'sda_app/signup.html', {'form': form})


@csrf_exempt
@require_POST
def send_otp_view(request):
    """Send OTP to email address"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        
        # Create and send OTP
        otp = OTPVerification.create_otp(email)
        success, message = OTPService.send_otp_email(email, otp.otp_code)
        
        if success:
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
        else:
            return JsonResponse({'success': False, 'message': message})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
@require_POST
def verify_otp_ajax_view(request):
    """Verify OTP via AJAX"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        otp_code = data.get('otp_code')
        
        if not email or not otp_code:
            return JsonResponse({'success': False, 'message': 'Email and OTP code are required'})
        
        try:
            otp_obj = OTPVerification.objects.filter(
                email=email,
                is_verified=False
            ).latest('created_at')
            
            is_valid, message = otp_obj.verify(otp_code)
            if is_valid:
                return JsonResponse({'success': True, 'message': 'Email verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': message})
                
        except OTPVerification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No valid OTP found for this email'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def verify_otp_view(request, email):
    """Handle OTP verification"""
    user = get_object_or_404(User, email=email)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST, email=email)
        if form.is_valid():
            # OTP is verified, activate user
            user.is_active = True
            user.save()
            
            # Send welcome email
            OTPService.send_welcome_email(user.email, user.username)
            
            # Login the user
            login(request, user)
            messages.success(request, 'Email verified successfully! Welcome to PaisaPro!')
            return redirect('dashboard')
    else:
        form = OTPVerificationForm(email=email)
    
    # Get the latest OTP for display purposes
    try:
        otp_obj = OTPVerification.objects.filter(email=email, is_verified=False).latest('created_at')
        otp_expires_at = otp_obj.expires_at
    except OTPVerification.DoesNotExist:
        otp_expires_at = None
    
    context = {
        'form': form,
        'email': email,
        'otp_expires_at': otp_expires_at,
    }
    return render(request, 'sda_app/verify_otp.html', context)


def resend_otp_view(request, email):
    """Handle OTP resending"""
    if request.method == 'POST':
        form = ResendOTPForm(request.POST)
        if form.is_valid():
            # Create new OTP
            otp = OTPVerification.create_otp(email)
            success, message = OTPService.send_otp_email(email, otp.otp_code)
            
            if success:
                messages.success(request, 'New verification code sent to your email!')
            else:
                messages.error(request, f'Failed to send verification code: {message}')
            
            return redirect('verify_otp', email=email)
    else:
        form = ResendOTPForm(initial={'email': email})
    
    return render(request, 'sda_app/resend_otp.html', {'form': form, 'email': email})


@login_required
def dashboard_view(request):
    """Dashboard view for logged-in users"""
    user = request.user
    account = user.account
    
    context = {
        'user': user,
        'account': account,
    }
    return render(request, 'sda_app/dashboard.html', context)


def home_view(request):
    """Home page view"""
    return render(request, 'sda_app/home.html')

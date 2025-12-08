from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
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
    """Handle user signup - accounts are automatically active"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Create user and automatically activate account
            user = form.save(commit=False)
            user.is_active = True  # Automatically activate the account
            user.save()
            
            # Create an Account instance for the new user (only if it doesn't exist)
            from .models import Account
            if not hasattr(user, 'account'):
                Account.objects.create(user=user)
            
            # Login the user
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to PaisaPro!')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'sda_app/signup.html', {'form': form})


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
    
    # Calculate financial metrics
    current_balance = account.current_balance
    monthly_income = account.monthly_income
    total_expenses = account.total_expenses
    savings = account.savings
    
    # Calculate savings rate
    savings_rate = 0
    if monthly_income > 0:
        savings_rate = (savings / monthly_income) * 100
    
    # Get recent transactions (mock data for now)
    recent_transactions = [
        {
            'description': 'Grocery Shopping',
            'amount': -85.50,
            'date': 'Today, 2:30 PM',
            'type': 'expense'
        },
        {
            'description': 'Salary Deposit',
            'amount': 3500.00,
            'date': 'Yesterday, 9:00 AM',
            'type': 'income'
        },
        {
            'description': 'Gas Station',
            'amount': -45.20,
            'date': 'Yesterday, 6:45 PM',
            'type': 'expense'
        },
        {
            'description': 'Netflix Subscription',
            'amount': -15.99,
            'date': '2 days ago',
            'type': 'expense'
        }
    ]
    
    # Get expense breakdown (mock data for now)
    expense_breakdown = [
        {'category': 'Food & Dining', 'amount': 450, 'percentage': 35},
        {'category': 'Transportation', 'amount': 320, 'percentage': 25},
        {'category': 'Entertainment', 'amount': 180, 'percentage': 20},
        {'category': 'Utilities', 'amount': 150, 'percentage': 15},
        {'category': 'Other', 'amount': 50, 'percentage': 5}
    ]
    
    # Get savings goals (mock data for now)
    savings_goals = [
        {'name': 'Emergency Fund', 'current': 2500, 'target': 5000, 'percentage': 50},
        {'name': 'Vacation Fund', 'current': 800, 'target': 2000, 'percentage': 40},
        {'name': 'New Car', 'current': 1200, 'target': 15000, 'percentage': 8}
    ]
    
    # Get financial tips
    financial_tips = [
        {
            'type': 'info',
            'icon': '💡',
            'title': 'Tip',
            'message': 'Consider setting up automatic transfers to your savings account on payday.'
        },
        {
            'type': 'success',
            'icon': '✅',
            'title': 'Good Job',
            'message': 'You\'re spending 15% less on dining out this month!'
        },
        {
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Alert',
            'message': 'Your entertainment budget is 80% used. Consider reducing spending.'
        }
    ]
    
    context = {
        'user': user,
        'account': account,
        'current_balance': current_balance,
        'monthly_income': monthly_income,
        'total_expenses': total_expenses,
        'savings': savings,
        'savings_rate': savings_rate,
        'recent_transactions': recent_transactions,
        'expense_breakdown': expense_breakdown,
        'savings_goals': savings_goals,
        'financial_tips': financial_tips,
    }
    return render(request, 'sda_app/dashboard.html', context)


def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Try to authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account is inactive. Please contact support.')
            else:
                # Try to find the user to provide better error message
                try:
                    user_exists = User.objects.get(username=username)
                    messages.error(request, 'Invalid password. Please try again.')
                except User.DoesNotExist:
                    try:
                        user_exists = User.objects.get(email=username)
                        messages.error(request, 'Invalid password. Please try again.')
                    except User.DoesNotExist:
                        messages.error(request, 'User not found. Please check your username/email.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'sda_app/login.html')


def home_view(request):
    """Home page view"""
    return render(request, 'sda_app/home.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .forms import (
    SignUpForm,
    OTPVerificationForm,
    ResendOTPForm,
    MonthlyIncomeForm,
    ExpenseForm,
    ProfileForm,
    EmailChangeStartForm,
    EmailChangeVerifyForm,
    AddSavingsForm,
    WithdrawSavingsForm,
    AddMoneyForm,
)
from .models import User, OTPVerification, OtherExpenses
from .email_service import OTPService
from .chatbot_service import FinancialChatbotService


def signup_view(request):
    """Handle user signup - users are active by default"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Create user (form already sets is_active=True)
            user = form.save()
            
            # Login the user
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to PaisaPro!')
            # Redirect to income setup after successful signup
            return redirect('income_setup')
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
            # Redirect to income setup after successful verification
            return redirect('income_setup')
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
    # If income not set, nudge user to set it
    if account.monthly_income == 0:
        return redirect('income_setup')
    
    # Calculate financial metrics
    current_balance = account.current_balance
    monthly_income = account.monthly_income
    total_expenses = account.total_expenses
    savings = account.savings
    
    # Calculate savings rate
    savings_rate = 0
    if monthly_income > 0:
        savings_rate = (savings / monthly_income) * 100
    
    # Recent transactions from real data (expenses only for now)
    expenses_qs = OtherExpenses.objects.filter(user=user).order_by('-date_timestamp')[:10]
    recent_transactions = [
        {
            'description': e.description,
            'amount': float(-e.amount),
            'date': e.expense_date.strftime('%b %d, %Y'),
            'type': 'expense',
            'category': e.category,
        }
        for e in expenses_qs
    ]
    
    # Expense breakdown from DB
    categories = dict(OtherExpenses._meta.get_field('category').choices)
    totals_by_category = {
        key: float(sum(e.amount for e in OtherExpenses.objects.filter(user=user, category=key)))
        for key in categories.keys()
    }
    grand_total = sum(totals_by_category.values()) or 1.0
    expense_breakdown = [
        {
            'category': categories[key],
            'amount': round(totals_by_category[key], 2),
            'percentage': round((totals_by_category[key] / grand_total) * 100, 2),
        }
        for key in categories.keys()
        if totals_by_category[key] > 0
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


@login_required
def income_setup_view(request):
    account = request.user.account
    
    # Check if user is skipping (coming from skip button)
    if request.GET.get('skip') == 'true':
        # Set a default income to prevent redirect loop
        account.monthly_income = 1000.00  # Default income
        # Only set balance equal to income if balance is currently 0
        if account.current_balance == 0:
            account.current_balance = account.monthly_income
        account.save()
        messages.info(request, 'Using default income. You can update it later in profile settings.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MonthlyIncomeForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            # Only set balance equal to income if balance is currently 0 (first time setup)
            if account.current_balance == 0:
                account.current_balance = account.monthly_income
                account.save()
            messages.success(request, 'Monthly income updated.')
            return redirect('dashboard')
    else:
        form = MonthlyIncomeForm(instance=account)
    return render(request, 'sda_app/income_setup.html', {'form': form})


@login_required
def add_expense_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            # Update account totals and subtract expense from balance
            account = request.user.account
            account.update_total_expenses()
            account.subtract_expense(expense.amount)
            messages.success(request, 'Expense added successfully.')
            return redirect('dashboard')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'sda_app/add_expense.html', {'form': form})


@login_required
def add_money_view(request):
    """Add money to current balance (salary, investment, etc.)"""
    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            money_type = form.cleaned_data['money_type']
            description = form.cleaned_data['description']
            
            account = request.user.account
            account.current_balance += amount
            account.save()
            
            type_display = dict(form.fields['money_type'].choices)[money_type]
            messages.success(request, f'{type_display} of ${amount} added to your balance!')
            return redirect('dashboard')
    else:
        form = AddMoneyForm()
    return render(request, 'sda_app/add_money.html', {'form': form})


@login_required
def add_savings_view(request):
    """Add money to savings"""
    if request.method == 'POST':
        form = AddSavingsForm(request.POST, user=request.user)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            add_all = form.cleaned_data['add_all']
            
            account = request.user.account
            
            if add_all:
                amount = account.current_balance
            
            if account.add_to_savings(amount):
                messages.success(request, f'${amount} added to savings!')
            else:
                messages.error(request, f'Cannot add ${amount} to savings. Current balance: ${account.current_balance}')
            return redirect('dashboard')
    else:
        form = AddSavingsForm(user=request.user)
    return render(request, 'sda_app/add_savings.html', {'form': form})


@login_required
def withdraw_savings_view(request):
    """Withdraw money from savings"""
    if request.method == 'POST':
        form = WithdrawSavingsForm(request.POST, user=request.user)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            account = request.user.account
            
            if account.withdraw_from_savings(amount):
                messages.success(request, f'${amount} withdrawn from savings!')
            else:
                messages.error(request, f'Cannot withdraw ${amount} from savings. Available savings: ${account.savings}')
            return redirect('dashboard')
    else:
        form = WithdrawSavingsForm(user=request.user)
    return render(request, 'sda_app/withdraw_savings.html', {'form': form})


@login_required
def profile_settings_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_settings')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'sda_app/profile_settings.html', {'form': form, 'email': user.email})


@login_required
def email_change_start_view(request):
    if request.method == 'POST':
        form = EmailChangeStartForm(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            otp = OTPVerification.create_otp(new_email)
            success, message = OTPService.send_otp_email(new_email, otp.otp_code)
            if success:
                messages.success(request, 'Verification code sent to new email.')
                return redirect('email_change_verify', email=new_email)
            messages.error(request, f'Failed to send verification code: {message}')
    else:
        form = EmailChangeStartForm()
    return render(request, 'sda_app/email_change_start.html', {'form': form})


@login_required
def email_change_verify_view(request, email):
    if request.method == 'POST':
        form = EmailChangeVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            try:
                otp_obj = OTPVerification.objects.filter(email=email, is_verified=False).latest('created_at')
            except OTPVerification.DoesNotExist:
                messages.error(request, 'No valid OTP found for this email.')
                return redirect('email_change_start')

            is_valid, message = otp_obj.verify(otp_code)
            if is_valid:
                user = request.user
                user.email = email
                user.save()
                messages.success(request, 'Email updated successfully.')
                return redirect('profile_settings')
            messages.error(request, message)
    else:
        form = EmailChangeVerifyForm(initial={'email': email})
    return render(request, 'sda_app/email_change_verify.html', {'form': form, 'email': email})


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
                    # Nudge income setup if not set
                    if user.account.monthly_income == 0:
                        return redirect('income_setup')
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


@login_required
def financial_chatbot_view(request):
    """Financial advisor chatbot endpoint"""
    if request.method == 'GET':
        message = request.GET.get('message', '').strip()
        if not message:
            return JsonResponse({'response': 'Please ask me a financial question!'})
        
        chatbot = FinancialChatbotService()
        response = chatbot.generate_response(message, request.user)
        return JsonResponse({'response': response})
    
    return JsonResponse({'response': 'Invalid request method'})


@login_required
def chatbot_tips_view(request):
    """Get personalized financial tips"""
    chatbot = FinancialChatbotService()
    tips = chatbot.get_quick_tips(request.user)
    return JsonResponse({'tips': tips})


def home_view(request):
    """Home page view"""
    return render(request, 'sda_app/home.html')

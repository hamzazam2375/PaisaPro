from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import User, Account, OtherExpenses
from .serializers import UserSerializer, AccountSerializer, ExpenseSerializer
from .email_service import OTPService
from .chatbot_service import FinancialChatbotService
from .financial_analyzer import FinancialAnalyzer
import random
from datetime import datetime, timedelta

# Auth APIs
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    """User registration with OTP"""
    try:
        email = request.data.get('email')
        username = request.data.get('username')
        
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user (inactive until OTP verified)
        user = User.objects.create_user(
            email=email,
            username=username,
            first_name=request.data.get('first_name'),
            last_name=request.data.get('last_name'),
            password=request.data.get('password'),
            is_active=False
        )
        
        # Generate and send OTP
        otp = str(random.randint(100000, 999999))
        from .models import OTPVerification
        OTPVerification.objects.create(email=email, otp_code=otp, purpose='signup')
        OTPService.send_otp_email(email, otp)
        
        return Response({'message': 'OTP sent to email'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_api(request):
    """Verify OTP and activate account"""
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        from .models import OTPVerification
        otp_record = OTPVerification.objects.filter(
            email=email,
            otp_code=otp,
            purpose='signup',
            is_verified=False
        ).first()
        
        if not otp_record or not otp_record.is_valid():
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate user
        user = User.objects.get(email=email)
        user.is_active = True
        user.save()
        
        # Create account
        Account.objects.create(user=user, current_balance=0, savings=0, monthly_income=0, total_expenses=0, budget_limit=0)
        
        otp_record.is_verified = True
        otp_record.save()
        
        # Send Paisa Pro membership welcome email
        OTPService.send_membership_email(user.email, user.get_full_name())
        
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_api(request):
    """Update user profile with email change support (requires OTP if email changed)"""
    try:
        user = request.user
        new_email = request.data.get('email')
        
        # Update name fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        
        # Check if email is being changed
        if new_email and new_email != user.email:
            # Check if new email already exists
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate and send OTP for email verification
            otp = str(random.randint(100000, 999999))
            from .models import OTPVerification
            OTPVerification.objects.create(email=new_email, otp_code=otp, purpose='email_change')
            OTPService.send_otp_email(new_email, otp)
            
            # Store pending email change in session
            request.session['pending_email_change'] = {
                'new_email': new_email,
                'user_id': user.id
            }
            
            user.save()
            return Response({
                'message': 'OTP sent to new email for verification',
                'requires_otp': True
            }, status=status.HTTP_200_OK)
        
        user.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email_change_api(request):
    """Verify OTP for email change"""
    try:
        otp = request.data.get('otp')
        pending_change = request.session.get('pending_email_change')
        
        if not pending_change:
            return Response({'error': 'No pending email change'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import OTPVerification
        otp_record = OTPVerification.objects.filter(
            email=pending_change['new_email'],
            otp_code=otp,
            purpose='email_change',
            is_verified=False
        ).first()
        
        if not otp_record or not otp_record.is_valid():
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update email
        user = User.objects.get(id=pending_change['user_id'])
        user.email = pending_change['new_email']
        user.save()
        
        otp_record.is_verified = True
        otp_record.save()
        
        # Clear session
        del request.session['pending_email_change']
        
        return Response({
            'message': 'Email updated successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """User login with email or username"""
    try:
        email_or_username = request.data.get('email')  # Can be email or username
        password = request.data.get('password')
        
        # Try to find user by email or username
        user_obj = None
        if '@' in email_or_username:
            # Looks like an email
            try:
                user_obj = User.objects.get(email=email_or_username)
            except User.DoesNotExist:
                pass
        else:
            # Looks like a username
            try:
                user_obj = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                pass
        
        # Authenticate using email (USERNAME_FIELD)
        if user_obj:
            user = authenticate(request, username=user_obj.email, password=password)
        else:
            user = None
        
        if user:
            login(request, user)
            # Mark that user has logged in at least once
            if user.is_first_login:
                user.is_first_login = False
                user.save()
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """User logout"""
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_api(request):
    """Delete user account and all associated data"""
    try:
        user = request.user
        
        # Django's CASCADE delete will handle related objects:
        # - Account (OneToOne)
        # - OtherExpenses (ForeignKey)
        # - Notification (ForeignKey)
        # - Any other models with ForeignKey to User
        
        # Delete user (this will cascade delete all related data)
        user.delete()
        
        # Log out after deletion
        logout(request)
        
        return Response({
            'message': 'Account and all associated data deleted successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Delete account error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def current_user_api(request):
    """Get current user info"""
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
    return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_api(request):
    """Send password reset OTP"""
    try:
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)
        
        otp = str(random.randint(100000, 999999))
        from .models import OTPVerification
        OTPVerification.objects.create(email=email, otp_code=otp, purpose='password_reset')
        OTPService.send_otp_email(email, otp)
        
        return Response({'message': 'Reset code sent to email'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_password_reset_otp_api(request):
    """Verify password reset OTP"""
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        from .models import OTPVerification
        otp_record = OTPVerification.objects.filter(
            email=email,
            otp_code=otp,
            purpose='password_reset',
            is_verified=False
        ).first()
        
        if not otp_record or not otp_record.is_valid():
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'OTP verified'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def set_new_password_api(request):
    """Set new password after OTP verification"""
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        from .models import OTPVerification
        otp_record = OTPVerification.objects.filter(
            email=email,
            otp_code=otp,
            purpose='password_reset',
            is_verified=False
        ).first()
        
        if not otp_record or not otp_record.is_valid():
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        
        otp_record.is_verified = True
        otp_record.save()
        
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_api(request):
    """Resend OTP"""
    try:
        email = request.data.get('email')
        otp = str(random.randint(100000, 999999))
        
        from .models import OTPVerification
        OTPVerification.objects.create(email=email, otp_code=otp, purpose='signup')
        OTPService.send_otp_email(email, otp)
        
        return Response({'message': 'OTP resent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Account APIs
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def account_api(request):
    """Get or update account details"""
    try:
        account = request.user.account
        
        if request.method == 'GET':
            return Response(AccountSerializer(account).data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = AccountSerializer(account, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """Get dashboard data"""
    try:
        user = request.user
        account = user.account
        
        # Calculate totals
        expenses = OtherExpenses.objects.filter(user=user)
        total_expenses = sum(exp.amount for exp in expenses)
        
        # Savings is a field in Account model
        total_savings = account.savings
        
        data = {
            'user': UserSerializer(user).data,
            'account': AccountSerializer(account).data,
            'total_expenses': total_expenses,
            'total_savings': total_savings,
            'recent_expenses': ExpenseSerializer(expenses.order_by('-expense_date')[:5], many=True).data,
        }
        
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Expense APIs
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expenses_api(request):
    """Get all expenses, add new expense, or delete expense"""
    try:
        user = request.user
        
        if request.method == 'GET':
            expenses = OtherExpenses.objects.filter(user=user).order_by('-expense_date')
            return Response(ExpenseSerializer(expenses, many=True).data, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            data = request.data.copy()
            # Remove user from data if present (will be set by save)
            data.pop('user', None)
            
            # Debug: Print received data
            print(f"DEBUG: Received expense data: {data}")
            print(f"DEBUG: Amount received: {data.get('amount')}, Type: {type(data.get('amount'))}")
            
            serializer = ExpenseSerializer(data=data)
            if serializer.is_valid():
                expense = serializer.save(user=user)
                print(f"DEBUG: Expense created with amount: {expense.amount}")
                # Deduct from account balance and update totals
                account = user.account
                account.subtract_expense(expense.amount)
                account.update_total_expenses()
                
                # Reload account to get updated totals
                account.refresh_from_db()
                
                # Check for unusual spending
                detect_unusual_expense(user, expense)
                
                # Check for budget overspending
                try:
                    check_budget_overspending(user, expense)
                except Exception as check_error:
                    print(f"Error in check_budget_overspending: {check_error}")
                
                return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def expense_detail_api(request, expense_id):
    """Delete a specific expense"""
    try:
        user = request.user
        
        try:
            expense = OtherExpenses.objects.get(id=expense_id, user=user)
            expense_amount = expense.amount
            
            # Delete the expense
            expense.delete()
            
            # Refund the amount to account balance
            account = user.account
            account.add_money(expense_amount)
            account.update_total_expenses()
            
            return Response({'message': 'Expense removed successfully', 'refunded_amount': expense_amount}, status=status.HTTP_200_OK)
        except OtherExpenses.DoesNotExist:
            return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Chatbot API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chatbot_api(request):
    """Handle chatbot conversation"""
    try:
        user_message = request.data.get('message')
        chatbot = FinancialChatbotService()
        response = chatbot.generate_response(user_message, request.user)
        return Response({'response': response}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Financial Insights API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_insights_api(request):
    """Get data-driven financial insights based on user's actual spending"""
    try:
        analyzer = FinancialAnalyzer(request.user)
        insights = analyzer.get_all_insights()
        
        # Generate data-driven insights
        spending_mistakes = analyzer.analyze_spending_mistakes()
        corrective_actions = analyzer.generate_corrective_actions(spending_mistakes)
        saving_tips = analyzer.generate_saving_tips()
        
        insights['spending_mistakes'] = spending_mistakes
        insights['corrective_actions'] = corrective_actions
        insights['saving_tips'] = saving_tips
        
        return Response(insights, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def income_setup_api(request):
    """Setup or update monthly income"""
    try:
        account = request.user.account
        monthly_income = request.data.get('monthly_income')
        
        if monthly_income is not None:
            account.monthly_income = monthly_income
            account.save()
            return Response({'message': 'Monthly income updated', 'account': AccountSerializer(account).data}, status=status.HTTP_200_OK)
        return Response({'error': 'Monthly income is required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_money_api(request):
    """Add money to current balance"""
    try:
        from decimal import Decimal
        account = request.user.account
        amount = request.data.get('amount')
        money_type = request.data.get('money_type', 'salary')
        
        if amount and float(amount) > 0:
            amount_decimal = Decimal(str(amount))
            account.current_balance += amount_decimal
            account.save()
            return Response({'message': 'Money added successfully', 'account': AccountSerializer(account).data}, status=status.HTTP_200_OK)
        return Response({'error': 'Please enter a valid positive amount'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_savings_api(request):
    """Add money to savings"""
    try:
        account = request.user.account
        amount = request.data.get('amount')
        
        if amount and float(amount) > 0:
            if account.add_to_savings(float(amount)):
                return Response({'message': 'Savings added successfully', 'account': AccountSerializer(account).data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Valid amount is required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_savings_api(request):
    """Withdraw money from savings"""
    try:
        account = request.user.account
        amount = request.data.get('amount')
        
        if amount and float(amount) > 0:
            if account.withdraw_from_savings(float(amount)):
                return Response({'message': 'Withdrawal successful', 'account': AccountSerializer(account).data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Insufficient savings'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Valid amount is required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def budget_api(request):
    """Get or set budget limit and category budgets"""
    try:
        from .serializers import CategoryBudgetSerializer
        from .models import CategoryBudget
        account = request.user.account
        
        if request.method == 'GET':
            # Get category budgets
            category_budgets = CategoryBudget.objects.filter(user=request.user)
            category_data = CategoryBudgetSerializer(category_budgets, many=True).data
            
            # Calculate budget usage percentage
            usage_percentage = 0
            if account.budget_limit > 0:
                usage_percentage = float((account.total_expenses / account.budget_limit) * 100)
            
            data = {
                'budget_limit': float(account.budget_limit),
                'total_expenses': float(account.total_expenses),
                'remaining': float(account.budget_remaining()),
                'is_over_budget': account.is_over_budget(),
                'usage_percentage': usage_percentage,
                'category_budgets': category_data
            }
            return Response(data, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            budget_limit = request.data.get('budget_limit')
            category_budgets = request.data.get('category_budgets', [])
            
            if budget_limit is not None:
                account.budget_limit = budget_limit
                account.save()
            
            # Update or create category budgets
            for cat_budget in category_budgets:
                if 'category' not in cat_budget or 'limit' not in cat_budget:
                    continue
                    
                CategoryBudget.objects.update_or_create(
                    user=request.user,
                    category=cat_budget['category'],
                    defaults={'limit': cat_budget['limit']}
                )
            
            # Return updated data
            category_budgets_updated = CategoryBudget.objects.filter(user=request.user)
            category_data = CategoryBudgetSerializer(category_budgets_updated, many=True).data
            
            return Response({
                'message': 'Budget updated successfully',
                'budget_limit': float(account.budget_limit),
                'category_budgets': category_data
            }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def spending_report_api(request):
    """Get spending report with category breakdown and analytics"""
    try:
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth
        from datetime import datetime, timedelta
        from decimal import Decimal
        
        user = request.user
        
        # Get filters from request
        start_date = request.GET.get('start_date') or request.data.get('start_date')
        end_date = request.GET.get('end_date') or request.data.get('end_date')
        category_filter = request.GET.get('category') or request.data.get('category')
        min_amount = request.GET.get('min_amount') or request.data.get('min_amount')
        max_amount = request.GET.get('max_amount') or request.data.get('max_amount')
        
        # Build query
        expenses = OtherExpenses.objects.filter(user=user)
        
        if start_date:
            expenses = expenses.filter(expense_date__gte=start_date)
        if end_date:
            expenses = expenses.filter(expense_date__lte=end_date)
        if category_filter:
            expenses = expenses.filter(category=category_filter)
        if min_amount:
            expenses = expenses.filter(amount__gte=Decimal(min_amount))
        if max_amount:
            expenses = expenses.filter(amount__lte=Decimal(max_amount))
        
        # Category totals
        category_totals = {}
        for expense in expenses:
            category = expense.category
            if category in category_totals:
                category_totals[category] += float(expense.amount)
            else:
                category_totals[category] = float(expense.amount)
        
        # Top spending categories (sorted by amount)
        top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Highest single transactions
        top_transactions = ExpenseSerializer(
            expenses.order_by('-amount')[:10], 
            many=True
        ).data
        
        # Monthly spending trend (last 6 months)
        six_months_ago = datetime.now().date() - timedelta(days=180)
        monthly_data = OtherExpenses.objects.filter(
            user=user,
            expense_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        monthly_trend = [
            {
                'month': item['month'].strftime('%Y-%m'),
                'total': float(item['total'])
            }
            for item in monthly_data
        ]
        
        # Income vs Expenses cashflow (current month + next 5 months = 6 months total)
        account = user.account
        cashflow_data = []
        current_date = datetime.now().date()
        
        # Start from current month and go to 5 months ahead (total 6 months)
        for i in range(6):
            # Calculate the target month
            month_offset = i
            year_offset = (current_date.month + month_offset - 1) // 12
            target_month = ((current_date.month + month_offset - 1) % 12) + 1
            target_year = current_date.year + year_offset
            
            month_start = datetime(target_year, target_month, 1).date()
            # Get last day of the month
            if target_month == 12:
                month_end = datetime(target_year, 12, 31).date()
            else:
                month_end = (datetime(target_year, target_month + 1, 1) - timedelta(days=1)).date()
            
            monthly_expenses = OtherExpenses.objects.filter(
                user=user,
                expense_date__gte=month_start,
                expense_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            cashflow_data.append({
                'month': month_start.strftime('%Y-%m'),
                'income': float(account.monthly_income),
                'expenses': float(monthly_expenses)
            })
        
        # Recent expenses
        recent_expenses = ExpenseSerializer(expenses.order_by('-expense_date')[:10], many=True).data
        
        data = {
            'total_expenses': float(sum(expense.amount for expense in expenses)),
            'category_breakdown': category_totals,
            'top_categories': top_categories,
            'top_transactions': top_transactions,
            'monthly_trend': monthly_trend,
            'cashflow_data': cashflow_data,
            'recent_expenses': recent_expenses,
            'expense_count': expenses.count()
        }
        
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """Get CSRF token for client"""
    return Response({'detail': 'CSRF cookie set'}, status=status.HTTP_200_OK)

# Notification APIs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications_api(request):
    """Get user notifications"""
    try:
        from .models import Notification
        # Get all notifications for the user
        all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        # Get unread count before slicing
        unread_count = all_notifications.filter(is_read=False).count()
        
        # Get latest 20 notifications
        notifications = all_notifications[:20]
        
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
        
        return Response({
            'notifications': data,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"DEBUG: Error in get_notifications_api: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read_api(request, notification_id):
    """Mark notification as read"""
    try:
        from .models import Notification
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read_api(request):
    """Mark all notifications as read"""
    try:
        from .models import Notification
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_all_notifications_api(request):
    """Clear all notifications"""
    try:
        from .models import Notification
        Notification.objects.filter(user=request.user).delete()
        return Response({'message': 'All notifications cleared'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Unusual Spending Detection
def detect_unusual_expense(user, expense):
    """Detect if expense is unusual based on user's history"""
    from .models import Notification
    from decimal import Decimal
    
    # Get user's expense history for this category
    similar_expenses = OtherExpenses.objects.filter(
        user=user,
        category=expense.category
    ).exclude(id=expense.id).order_by('-expense_date')[:30]
    
    if similar_expenses.count() < 3:
        # Not enough history to detect unusual spending
        return False
    
    # Calculate average and standard deviation
    amounts = [float(e.amount) for e in similar_expenses]
    avg_amount = sum(amounts) / len(amounts)
    
    # Simple threshold: 2x average or 3x median
    threshold = avg_amount * 2
    
    if float(expense.amount) > threshold:
        # Create notification
        Notification.create_unusual_spending_alert(
            user=user,
            expense=expense,
            reason=f"This is {float(expense.amount)/avg_amount:.1f}x higher than your average {expense.category} expense (${avg_amount:.2f})"
        )
        return True
    
    return False

def check_budget_overspending(user, expense):
    """Check if expense causes budget overspending and create notification"""
    from .models import Notification, CategoryBudget
    from django.db.models import Sum
    from datetime import timedelta
    from django.utils import timezone
    
    account = user.account
    
    print(f"DEBUG: Checking budget - Limit: {account.budget_limit}, Total Expenses: {account.total_expenses}")
    
    # Check total budget
    if account.budget_limit > 0 and account.total_expenses > account.budget_limit:
        print(f"DEBUG: Budget exceeded! Creating notification...")
        # Check if similar notification was created in last 24 hours to avoid duplicates
        recent_notification = Notification.objects.filter(
            user=user,
            notification_type='budget_alert',
            title='💰 Budget Limit Exceeded',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).exists()
        
        if not recent_notification:
            notification = Notification.objects.create(
                user=user,
                title='💰 Budget Limit Exceeded',
                message=f'Your total expenses (Rs.{account.total_expenses:.2f}) have exceeded your budget limit (Rs.{account.budget_limit:.2f}).',
                notification_type='budget_alert'
            )
            print(f"DEBUG: Notification created with ID: {notification.id}")
        else:
            print(f"DEBUG: Skipping notification - recent one already exists")
    
    # Check category budget
    try:
        category_budget = CategoryBudget.objects.get(user=user, category=expense.category)
        category_spent = OtherExpenses.objects.filter(
            user=user,
            category=expense.category
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if category_spent > category_budget.limit:
            # Check for duplicate category budget notification
            recent_category_notification = Notification.objects.filter(
                user=user,
                notification_type='budget_alert',
                title='⚠️ Category Budget Exceeded',
                message__contains=expense.category,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).exists()
            
            if not recent_category_notification:
                Notification.objects.create(
                    user=user,
                    title='⚠️ Category Budget Exceeded',
                    message=f'Your {expense.category} expenses (Rs.{category_spent:.2f}) have exceeded the budget limit (Rs.{category_budget.limit:.2f}).',
                    notification_type='budget_alert'
                )
    except CategoryBudget.DoesNotExist:
        pass

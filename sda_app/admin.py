from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Account, OtherExpenses, MonthlySummary, Recommendation, Alert, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_active', 'is_staff', 'date_joined']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin interface for Account model"""
    list_display = ['user', 'current_balance', 'savings', 'monthly_income', 'total_expenses', 'budget_limit']
    search_fields = ['user__username', 'user__email']
    list_filter = ['user']
    readonly_fields = ['user']


@admin.register(OtherExpenses)
class OtherExpensesAdmin(admin.ModelAdmin):
    """Admin interface for OtherExpenses model"""
    list_display = ['user', 'category', 'amount', 'expense_date', 'description', 'date_timestamp']
    search_fields = ['user__username', 'description']
    list_filter = ['category', 'expense_date', 'user']
    date_hierarchy = 'expense_date'


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    """Admin interface for MonthlySummary model"""
    list_display = ['user', 'period_month', 'total_income', 'total_expenses', 'savings_achieved']
    search_fields = ['user__username']
    list_filter = ['period_month', 'user']
    date_hierarchy = 'period_month'


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Admin interface for Recommendation model"""
    list_display = ['user', 'message', 'created_at']
    search_fields = ['user__username', 'message']
    list_filter = ['created_at', 'user']
    date_hierarchy = 'created_at'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin interface for Alert model"""
    list_display = ['user', 'alert_type', 'message', 'read', 'created_at']
    search_fields = ['user__username', 'message']
    list_filter = ['alert_type', 'read', 'created_at', 'user']
    date_hierarchy = 'created_at'


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """Admin interface for OTPVerification model"""
    list_display = ['email', 'otp_code', 'purpose', 'is_verified', 'created_at', 'expires_at', 'attempts']
    search_fields = ['email']
    list_filter = ['purpose', 'is_verified', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'expires_at']

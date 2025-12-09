from rest_framework import serializers
from .models import User, Account, OtherExpenses, MonthlySummary, Recommendation, CategoryBudget

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_first_login']
        read_only_fields = ['id', 'date_joined', 'is_first_login']

class AccountSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(source='current_balance', max_digits=12, decimal_places=2, read_only=True)
    savings_balance = serializers.DecimalField(source='savings', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Account
        fields = ['id', 'current_balance', 'available_balance', 'savings', 'savings_balance', 'monthly_income', 'total_expenses', 'budget_limit']
        read_only_fields = ['id', 'available_balance', 'savings_balance']

class ExpenseSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True, default='')
    
    class Meta:
        model = OtherExpenses
        fields = ['id', 'category', 'amount', 'expense_date', 'description', 'date_timestamp']
        read_only_fields = ['id', 'date_timestamp']

class MonthlySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlySummary
        fields = ['id', 'user', 'period_month', 'total_income', 'total_expenses', 'savings_achieved', 'overspending_categories', 'warnings']
        read_only_fields = ['id']

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ['id', 'user', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

class CategoryBudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoryBudget
        fields = ['id', 'category', 'limit', 'spent', 'remaining', 'usage_percentage', 'is_over_budget']
        read_only_fields = ['id', 'spent', 'remaining', 'usage_percentage', 'is_over_budget']
    
    def get_spent(self, obj):
        return float(obj.get_spent())
    
    def get_remaining(self, obj):
        return float(obj.get_remaining())
    
    def get_usage_percentage(self, obj):
        return float(obj.get_usage_percentage())
    
    def get_is_over_budget(self, obj):
        return obj.is_over_budget()

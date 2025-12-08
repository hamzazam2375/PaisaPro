from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal
import random
import string
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser): 
    """AbstractUser is a base class for all user models in Django and it provides username,
     password, email, first_name, last_name, is_active, is_staff, is_superuser, last_login, 
     date_joined"""
    """User model extending Django's AbstractUser"""
    
    def get_full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.get_full_name() or self.username


class Account(models.Model):
    """Account model representing user's financial account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    savings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    def calculate_balance(self):
        """Calculate current balance based on income and expenses"""
        return self.monthly_income - self.total_expenses
    
    def update_total_expenses(self):
        """Update total expenses from all user expenses"""
        other_expenses = sum(expense.amount for expense in self.user.other_expenses.all())
        shopping_expenses = sum(expense.amount for expense in self.user.shopping_lists.all())
        self.total_expenses = other_expenses + shopping_expenses
        self.save()
    
    def update_current_balance(self):
        """Update current balance by subtracting new expenses"""
        # Don't recalculate from income, just update expenses total
        self.update_total_expenses()
        # Current balance should only decrease when expenses are added
        # It should not be recalculated from income - expenses
    
    def add_salary(self):
        """Add monthly income to current balance"""
        self.current_balance += self.monthly_income
        self.save()
    
    def subtract_expense(self, expense_amount):
        """Subtract expense amount from current balance"""
        self.current_balance -= expense_amount
        self.save()
    
    def add_to_savings(self, amount):
        """Add amount to savings and subtract from current balance"""
        if amount <= self.current_balance:
            self.savings += amount
            self.current_balance -= amount
            self.save()
            return True
        return False
    
    def withdraw_from_savings(self, amount):
        """Withdraw amount from savings and add to current balance"""
        if amount <= self.savings:
            self.savings -= amount
            self.current_balance += amount
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Account"


class Expense(models.Model):
    """Base expense model - Django abstract base class"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date_timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    
    class Meta:
        abstract = True
    
    def get_expense_type(self):
        """Method that should be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_expense_type()")
    
    def validate_expense(self):
        """Method for expense validation logic that should be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement validate_expense()")
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"


class OtherExpenses(Expense):
    """Other expenses subclass of Expense"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='other_expenses')
    # User-provided date for the expense entry; differs from created timestamp
    expense_date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=50, choices=[
        ('food', 'Food'),
        ('transportation', 'Transportation'),
        ('entertainment', 'Entertainment'),
        ('utilities', 'Utilities'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('other', 'Other'),
    ])
    
    def get_expense_type(self):
        """Return the type of expense"""
        return f"Other Expense - {self.category}"
    
    def validate_expense(self):
        """Validate other expenses"""
        if self.amount <= 0:
            raise ValueError("Expense amount must be positive")
        if not self.category:
            raise ValueError("Category is required for other expenses")
        return True
    
    def __str__(self):
        return f"{self.category}: {self.description} - ${self.amount}"


class Website(models.Model):
    """Website model for product price comparison"""
    name = models.CharField(max_length=100)
    url = models.URLField()
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for shopping list items"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    websites = models.ManyToManyField(Website, related_name='products', blank=True)
    
    def get_cheapest_price(self):
        """Get the cheapest price for this product across all websites"""
        return self.price  # In a real implementation, this would check multiple websites
    
    def __str__(self):
        return self.name


class ShoppingList(Expense):
    """Shopping list subclass of Expense"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_lists')
    products = models.ManyToManyField(Product, related_name='shopping_lists')
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def get_expense_type(self):
        """Return the type of expense"""
        return "Shopping List"
    
    def validate_expense(self):
        """Validate shopping list expenses"""
        if self.amount <= 0:
            raise ValueError("Shopping list amount must be positive")
        if not self.products.exists():
            raise ValueError("Shopping list must contain at least one product")
        return True
    
    def calculate_total(self):
        """Calculate total cost of all products in the shopping list"""
        total = sum(product.price for product in self.products.all())
        self.product_price = total
        self.amount = total
        self.save()
        return total
    
    def __str__(self):
        return f"Shopping List: {self.description} - ${self.amount}"


class MonthlySummary(models.Model):
    """Monthly summary model for financial analysis"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_summaries')
    period_month = models.DateField()
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    savings_achieved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    overspending_categories = models.JSONField(default=list, blank=True)
    warnings = models.TextField(blank=True)
    
    def calculate_savings(self):
        """Calculate savings achieved for the month"""
        self.savings_achieved = self.total_income - self.total_expenses
        self.save()
        return self.savings_achieved
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.period_month.strftime('%B %Y')}"


class SentimentAnalysis(models.Model):
    """Sentiment analysis model for company reviews"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sentiment_analyses')
    company = models.CharField(max_length=100)
    reviews = models.TextField()
    sentiment_score = models.FloatField(default=0.0)  # -1 to 1 scale
    analysis_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Sentiment Analysis for {self.company}"


class Chatbot(models.Model):
    """Chatbot model for AI assistance"""
    monthly_summaries = models.ManyToManyField(MonthlySummary, related_name='chatbot_sessions', blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    last_interaction = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chatbot Session {self.session_id}"


class Recommendation(models.Model):
    """Recommendation model for financial advice"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)
    
    def __str__(self):
        return f"Recommendation for {self.user.get_full_name() or self.user.username}"


class Alert(models.Model):
    """Alert model for notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    alert_type = models.CharField(max_length=50, choices=[
        ('budget_exceeded', 'Budget Exceeded'),
        ('unusual_expense', 'Unusual Expense'),
        ('savings_goal', 'Savings Goal'),
        ('monthly_summary', 'Monthly Summary'),
    ], default='budget_exceeded')
    
    def __str__(self):
        return f"Alert for {self.user.get_full_name() or self.user.username}: {self.message}"


class OTPVerification(models.Model):
    """OTP verification model for email verification during signup"""
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set expiry time when creating new OTP
            self.expires_at = timezone.now() + timedelta(minutes=10)  # OTP expires in 10 minutes
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for the given email"""
        # Delete any existing unverified OTPs for this email
        cls.objects.filter(email=email, is_verified=False).delete()
        
        # Generate new OTP
        otp_code = cls.generate_otp()
        otp = cls.objects.create(email=email, otp_code=otp_code)
        return otp
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not verified)"""
        return not self.is_verified and timezone.now() <= self.expires_at
    
    def verify(self, input_otp):
        """Verify the OTP code"""
        self.attempts += 1
        self.save()
        
        if not self.is_valid():
            return False, "OTP has expired or already been used"
        
        if self.otp_code == input_otp:
            self.is_verified = True
            self.save()
            return True, "OTP verified successfully"
        else:
            return False, "Invalid OTP code"
    
    def __str__(self):
        return f"OTP for {self.email} - {'Verified' if self.is_verified else 'Pending'}"
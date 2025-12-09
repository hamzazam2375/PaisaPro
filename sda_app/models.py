from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random
import string


class User(AbstractUser):
    """User model extending Django's AbstractUser with custom methods"""
    email = models.EmailField(unique=True)  # Make email unique and required
    is_first_login = models.BooleanField(default=True)  # Track if user has logged in before
    
    # Allow login with email or username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
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
    budget_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Monthly budget limit for expenses")
    
    def calculate_balance(self):
        """Calculate current balance based on income and expenses"""
        return self.monthly_income - self.total_expenses
    
    def is_over_budget(self):
        """Check if expenses exceed budget limit"""
        if self.budget_limit > 0:
            return self.total_expenses > self.budget_limit
        return False
    
    def budget_remaining(self):
        """Calculate remaining budget"""
        if self.budget_limit > 0:
            return self.budget_limit - self.total_expenses
        return 0
    
    def update_total_expenses(self):
        """Update total expenses from all user expenses"""
        other_expenses = sum(expense.amount for expense in self.user.other_expenses.all())
        self.total_expenses = other_expenses
        self.save()
    
    def update_current_balance(self):
        """Update current balance by subtracting new expenses"""
        self.update_total_expenses()
    
    def add_salary(self):
        """Add monthly income to current balance"""
        self.current_balance += self.monthly_income
        self.save()
    
    def subtract_expense(self, expense_amount):
        """Subtract expense amount from current balance"""
        from decimal import Decimal
        expense_amount = Decimal(str(expense_amount))
        self.current_balance -= expense_amount
        self.save()
    
    def add_to_savings(self, amount):
        """Add amount to savings and subtract from current balance"""
        from decimal import Decimal
        amount = Decimal(str(amount))
        if amount <= self.current_balance:
            self.savings += amount
            self.current_balance -= amount
            self.save()
            return True
        return False
    
    def withdraw_from_savings(self, amount):
        """Withdraw amount from savings and add to current balance"""
        from decimal import Decimal
        amount = Decimal(str(amount))
        if amount <= self.savings:
            self.savings -= amount
            self.current_balance += amount
            self.save()
            return True
        return False
    
    def add_money(self, amount):
        """Add money to current balance (used for refunds, adding money, etc.)"""
        from decimal import Decimal
        amount = Decimal(str(amount))
        self.current_balance += amount
        self.save()
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Account"


class Expense(models.Model):
    """Base expense model - Django abstract base class"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    date_timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')
    
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
    expense_date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=50, choices=[
        ('food', 'Food'),
        ('transportation', 'Transportation'),
        ('entertainment', 'Entertainment'),
        ('utilities', 'Utilities'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('shopping', 'Shopping'),
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


class CategoryBudget(models.Model):
    """Category-wise budget limits"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_budgets')
    category = models.CharField(max_length=50, choices=[
        ('food', 'Food'),
        ('transportation', 'Transportation'),
        ('entertainment', 'Entertainment'),
        ('utilities', 'Utilities'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('shopping', 'Shopping'),
        ('other', 'Other'),
    ])
    limit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    class Meta:
        unique_together = ('user', 'category')
        verbose_name = "Category Budget"
        verbose_name_plural = "Category Budgets"
    
    def get_spent(self):
        """Calculate total spent in this category"""
        expenses = OtherExpenses.objects.filter(user=self.user, category=self.category)
        return sum(expense.amount for expense in expenses)
    
    def get_remaining(self):
        """Calculate remaining budget for this category"""
        return self.limit - self.get_spent()
    
    def is_over_budget(self):
        """Check if spending exceeds the category budget"""
        return self.get_spent() > self.limit
    
    def get_usage_percentage(self):
        """Get budget usage percentage"""
        spent = self.get_spent()
        if self.limit > 0:
            return (spent / self.limit) * 100
        return 0
    
    def __str__(self):
        return f"{self.user.username} - {self.category}: ${self.limit}"


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


class Recommendation(models.Model):
    """Recommendation model for financial advice"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
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


class PriceCache(models.Model):
    """Cache for scraped product prices to reduce scraping time"""
    product_name = models.CharField(max_length=255, db_index=True)
    source = models.CharField(max_length=50)  # alfatah, daraz, imtiaz
    price_pkr = models.DecimalField(max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(max_length=500)
    scraped_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Price Cache"
        verbose_name_plural = "Price Caches"
        indexes = [
            models.Index(fields=['product_name', 'source']),
            models.Index(fields=['scraped_at']),
        ]
    
    def is_stale(self):
        """Check if cache is older than 24 hours"""
        return timezone.now() - self.scraped_at > timedelta(hours=24)
    
    @classmethod
    def get_cached_price(cls, product_name, source):
        """Get cached price if not stale"""
        try:
            cache = cls.objects.filter(
                product_name__iexact=product_name,
                source=source
            ).latest('scraped_at')
            
            if not cache.is_stale():
                return cache
        except cls.DoesNotExist:
            pass
        return None
    
    @classmethod
    def clean_old_cache(cls):
        """Delete cache entries older than 24 hours"""
        cutoff_time = timezone.now() - timedelta(hours=24)
        cls.objects.filter(scraped_at__lt=cutoff_time).delete()
    
    def __str__(self):
        return f"{self.product_name} - {self.source} (${self.price_usd})"


class Notification(models.Model):
    """In-app notifications for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=[
        ('unusual_spending', 'Unusual Spending'),
        ('budget_alert', 'Budget Alert'),
        ('savings_goal', 'Savings Goal'),
        ('general', 'General'),
    ])
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()
    
    @classmethod
    def create_unusual_spending_alert(cls, user, expense, reason):
        """Create unusual spending notification"""
        return cls.objects.create(
            user=user,
            title='⚠️ Unusual Spending Detected',
            message=f'An unusual expense of ${expense.amount} was detected in {expense.category}. {reason}',
            notification_type='unusual_spending'
        )
    
    @classmethod
    def create_budget_alert(cls, user, category, amount, limit):
        """Create budget exceeded notification"""
        return cls.objects.create(
            user=user,
            title='💰 Budget Alert',
            message=f'You have exceeded your {category} budget. Spent: ${amount}, Limit: ${limit}',
            notification_type='budget_alert'
        )
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class OTPVerification(models.Model):
    """OTP verification model for email verification during signup and password reset"""
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    purpose = models.CharField(max_length=20, default='signup', choices=[
        ('signup', 'Signup'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
    ])
    
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

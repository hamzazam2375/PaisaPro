from decimal import Decimal
from django.db.models import Sum, Avg, Count
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict


class FinancialAnalyzer:
    """Analyze user financial data and provide data-driven insights"""
    
    def __init__(self, user):
        self.user = user
        self.account = user.account
    
    def get_all_insights(self):
        """Get all financial insights"""
        from .models import OtherExpenses
        
        # Get expenses for current month
        current_month = date.today().replace(day=1)
        expenses = OtherExpenses.objects.filter(
            user=self.user,
            expense_date__gte=current_month
        )
        
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Category breakdown
        category_breakdown = expenses.values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        insights = {
            'total_expenses': float(total_expenses),
            'monthly_income': float(self.account.monthly_income),
            'current_balance': float(self.account.current_balance),
            'savings': float(self.account.savings),
            'budget_limit': float(self.account.budget_limit),
            'budget_remaining': float(self.account.budget_remaining()),
            'is_over_budget': self.account.is_over_budget(),
            'category_breakdown': [
                {
                    'category': item['category'],
                    'total': float(item['total'])
                }
                for item in category_breakdown
            ],
            'recommendations': self._generate_recommendations(total_expenses)
        }
        
        return insights
    
    def _generate_recommendations(self, total_expenses):
        """Generate financial recommendations"""
        recommendations = []
        
        # Budget recommendation
        if self.account.budget_limit > 0:
            budget_usage = (total_expenses / self.account.budget_limit) * 100
            if budget_usage > 90:
                recommendations.append({
                    'type': 'warning',
                    'message': f'You\'ve used {budget_usage:.1f}% of your budget. Consider reducing expenses.'
                })
            elif budget_usage > 75:
                recommendations.append({
                    'type': 'info',
                    'message': f'You\'ve used {budget_usage:.1f}% of your budget. Monitor your spending closely.'
                })
        
        # Savings recommendation
        if self.account.monthly_income > 0:
            savings_rate = (self.account.savings / self.account.monthly_income) * 100
            if savings_rate < 10:
                recommendations.append({
                    'type': 'tip',
                    'message': 'Try to save at least 10-20% of your monthly income.'
                })
        
        # Income recommendation
        if self.account.monthly_income == 0:
            recommendations.append({
                'type': 'action',
                'message': 'Set up your monthly income to get better financial insights.'
            })
        
        return recommendations
    
    def analyze_spending_mistakes(self):
        """Analyze spending mistakes based on actual user data"""
        from .models import OtherExpenses, CategoryBudget
        
        mistakes = []
        current_month_start = date.today().replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Get current and previous month expenses
        current_expenses = OtherExpenses.objects.filter(
            user=self.user,
            expense_date__gte=current_month_start
        )
        
        previous_expenses = OtherExpenses.objects.filter(
            user=self.user,
            expense_date__gte=last_month_start,
            expense_date__lt=current_month_start
        )
        
        if not current_expenses.exists():
            return []
        
        # 1. UNUSUAL SPENDING: Category spikes compared to past averages
        for category in ['food', 'transportation', 'entertainment', 'utilities', 'healthcare', 'education', 'other']:
            current_cat_total = current_expenses.filter(category=category).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            # Calculate historical average (last 3 months excluding current)
            three_months_ago = current_month_start - relativedelta(months=3)
            historical_avg = OtherExpenses.objects.filter(
                user=self.user,
                category=category,
                expense_date__gte=three_months_ago,
                expense_date__lt=current_month_start
            ).aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
            
            if historical_avg > 0 and current_cat_total > historical_avg * 2:
                mistakes.append({
                    'type': 'unusual_spending',
                    'severity': 'high',
                    'description': f'{category.capitalize()} spending is {float(current_cat_total/historical_avg):.1f}x higher than your 3-month average of ${float(historical_avg):.2f}',
                    'amount': float(current_cat_total),
                    'category': category
                })
        
        # 2. OVERSPENDING: Exceeding budgets
        if self.account.budget_limit > 0 and self.account.total_expenses > self.account.budget_limit:
            overspend_amount = self.account.total_expenses - self.account.budget_limit
            mistakes.append({
                'type': 'overspending',
                'severity': 'critical',
                'description': f'Exceeded total budget by ${float(overspend_amount):.2f} (${float(self.account.total_expenses):.2f} spent of ${float(self.account.budget_limit):.2f} limit)',
                'amount': float(overspend_amount),
                'category': 'total'
            })
        
        # Check category budget overspending
        category_budgets = CategoryBudget.objects.filter(user=self.user)
        for cat_budget in category_budgets:
            cat_spent = current_expenses.filter(category=cat_budget.category).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            if cat_spent > cat_budget.limit:
                overspend = cat_spent - cat_budget.limit
                mistakes.append({
                    'type': 'overspending',
                    'severity': 'high',
                    'description': f'{cat_budget.category.capitalize()} budget exceeded by ${float(overspend):.2f} (${float(cat_spent):.2f} spent of ${float(cat_budget.limit):.2f} limit)',
                    'amount': float(cat_spent),
                    'category': cat_budget.category
                })
        
        # 3. UNNECESSARY EXPENSES: Small repeated purchases that add up
        small_expenses = current_expenses.filter(amount__lt=50).order_by('category', 'expense_date')
        
        # Group by category and count
        category_counts = defaultdict(list)
        for expense in small_expenses:
            category_counts[expense.category].append(float(expense.amount))
        
        for category, amounts in category_counts.items():
            if len(amounts) >= 5:  # 5 or more small transactions
                total_small = sum(amounts)
                if total_small > 100:  # Adds up to significant amount
                    mistakes.append({
                        'type': 'unnecessary_expenses',
                        'severity': 'medium',
                        'description': f'{len(amounts)} small {category} purchases totaling ${total_small:.2f} - consider consolidating or reducing',
                        'amount': total_small,
                        'category': category
                    })
        
        return mistakes
    
    def generate_corrective_actions(self, mistakes):
        """Generate specific corrective actions based on detected mistakes"""
        actions = []
        
        if not mistakes:
            return []
        
        for mistake in mistakes:
            if mistake['type'] == 'unusual_spending':
                actions.append(f"Review your {mistake['category']} expenses and identify what caused the spike of ${mistake['amount']:.2f}")
            
            elif mistake['type'] == 'overspending':
                if mistake['category'] == 'total':
                    actions.append(f"Reduce spending by ${mistake['amount']:.2f} to stay within your overall budget")
                else:
                    actions.append(f"Cut back on {mistake['category']} expenses to get back under your ${mistake['amount']:.2f} budget")
            
            elif mistake['type'] == 'unnecessary_expenses':
                actions.append(f"Reduce frequency of small {mistake['category']} purchases - they added up to ${mistake['amount']:.2f} this month")
        
        return list(set(actions))  # Remove duplicates
    
    def generate_saving_tips(self):
        """Generate personalized saving tips based on actual spending patterns"""
        from .models import OtherExpenses
        
        tips = []
        current_month_start = date.today().replace(day=1)
        
        current_expenses = OtherExpenses.objects.filter(
            user=self.user,
            expense_date__gte=current_month_start
        )
        
        if not current_expenses.exists():
            return []
        
        # Analyze category spending
        category_totals = current_expenses.values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        for cat_data in category_totals:
            category = cat_data['category']
            total = float(cat_data['total'])
            count = cat_data['count']
            
            # High spending categories
            if total > 500:  # Significant spending
                avg_per_transaction = total / count
                if category == 'food' and count > 15:
                    tips.append(f"You spent ${total:.2f} on food across {count} transactions. Meal planning could reduce this by 20-30%")
                elif category == 'entertainment' and total > 300:
                    tips.append(f"Entertainment costs ${total:.2f} this month. Consider free alternatives to save ${(total * 0.3):.2f}")
                elif category == 'transportation' and avg_per_transaction > 30:
                    tips.append(f"Average ${avg_per_transaction:.2f} per transportation expense. Carpooling or public transit could cut this significantly")
        
        # Check if income exists for savings rate calculation
        if self.account.monthly_income > 0:
            current_savings_rate = (self.account.savings / self.account.monthly_income) * 100
            
            if current_savings_rate < 20:
                potential_savings = float(self.account.monthly_income) * 0.20 - float(self.account.savings)
                if potential_savings > 0:
                    tips.append(f"Currently saving {current_savings_rate:.1f}% of income. Increase by ${potential_savings:.2f}/month to reach 20% savings goal")
        
        # High frequency, low-value purchases
        small_frequent = current_expenses.filter(amount__lt=20).count()
        if small_frequent > 10:
            small_total = float(current_expenses.filter(amount__lt=20).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0'))
            tips.append(f"{small_frequent} small purchases totaled ${small_total:.2f}. Reducing by half could save ${(small_total/2):.2f}")
        
        return tips
    
    def get_financial_health_score(self):
        """Calculate financial health score (0-100)"""
        score = 50  # Base score
        
        # Positive factors
        if self.account.savings > 0:
            score += 15
        
        if self.account.monthly_income > 0 and self.account.total_expenses < self.account.monthly_income:
            score += 20
        
        if not self.account.is_over_budget():
            score += 15
        
        # Negative factors
        if self.account.current_balance < 0:
            score -= 30
        
        if self.account.is_over_budget():
            score -= 20
        
        return max(0, min(100, score))
    
    def save_recommendations_to_db(self):
        """Save recommendations to database"""
        from .models import Recommendation
        
        insights = self.get_all_insights()
        for rec in insights['recommendations']:
            Recommendation.objects.create(
                user=self.user,
                message=rec['message']
            )

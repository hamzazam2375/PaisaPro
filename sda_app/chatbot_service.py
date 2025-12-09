import os
import re
from django.conf import settings
from django.contrib.auth.models import User
from .models import Account, OtherExpenses

# Try to import openai, but don't fail if it's not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class FinancialChatbotService:
    def __init__(self):
        # Set OpenAI API key from environment or settings
        self.api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, 'OPENAI_API_KEY', None)
        if self.api_key:
            openai.api_key = self.api_key
    
    def is_financial_question(self, message):
        """Check if the question is related to financial advice"""
        financial_keywords = [
            'saving', 'savings', 'budget', 'budgeting', 'finance', 'financial',
            'expense', 'expenses', 'spending', 'money', 'income', 'salary',
            'investment', 'invest', 'investing', 'loan', 'debt', 'credit',
            'cash', 'dollar', 'rupee', 'currency', 'wealth', 'rich', 'poor',
            'afford', 'expensive', 'cheap', 'cost', 'price', 'pay', 'payment',
            'bank', 'account', 'balance', 'withdraw', 'deposit', 'transfer',
            'retirement', 'pension', 'emergency', 'fund', 'goal', 'target',
            'plan', 'planning', 'strategy', 'tip', 'advice', 'suggestion',
            'help', 'improve', 'increase', 'decrease', 'reduce', 'cut',
            'manage', 'control', 'track', 'monitor', 'analyze', 'review'
        ]
        
        # Convert to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Check for financial keywords
        keyword_matches = sum(1 for keyword in financial_keywords if keyword in message_lower)
        
        # Check for financial question patterns
        financial_patterns = [
            r'\b(how|what|when|where|why|which)\b.*\b(save|spend|invest|budget|finance)\b',
            r'\b(save|spend|invest|budget|finance)\b.*\b(how|what|when|where|why|which)\b',
            r'\b(money|dollar|rupee|cash)\b',
            r'\b(income|salary|wage|earn)\b',
            r'\b(expense|cost|price|pay)\b',
            r'\b(rich|wealth|poor|broke)\b',
            r'\b(afford|expensive|cheap)\b'
        ]
        
        pattern_matches = sum(1 for pattern in financial_patterns if re.search(pattern, message_lower))
        
        # Consider it financial if it has keywords or patterns
        return keyword_matches > 0 or pattern_matches > 0
    
    def get_user_financial_context(self, user):
        """Get user's financial data for context"""
        try:
            account = user.account
            expenses = OtherExpenses.objects.filter(user=user).order_by('-date_timestamp')[:5]
            
            context = {
                'monthly_income': float(account.monthly_income),
                'current_balance': float(account.current_balance),
                'savings': float(account.savings),
                'total_expenses': float(account.total_expenses),
                'recent_expenses': [
                    {
                        'amount': float(expense.amount),
                        'category': expense.category,
                        'description': expense.description,
                        'date': expense.expense_date.strftime('%Y-%m-%d')
                    }
                    for expense in expenses
                ]
            }
            return context
        except:
            return None
    
    def generate_response(self, message, user=None):
        """Generate AI response for financial questions"""
        # Check if question is financial
        if not self.is_financial_question(message):
            return "I'm a financial advisor. Please ask me questions about saving money, budgeting, investments, expenses, or other financial topics."
        
        # If OpenAI is not available, provide fallback responses
        if not OPENAI_AVAILABLE or not self.api_key:
            return self.get_fallback_response(message, user)
        
        # Get user's financial context if available
        user_context = ""
        if user and hasattr(user, 'account'):
            context = self.get_user_financial_context(user)
            if context:
                user_context = f"""
                User's Financial Profile:
                - Monthly Income: ${context['monthly_income']:,.2f}
                - Current Balance: ${context['current_balance']:,.2f}
                - Savings: ${context['savings']:,.2f}
                - Total Expenses: ${context['total_expenses']:,.2f}
                - Recent Expenses: {context['recent_expenses']}
                """
        
        # Create comprehensive prompt
        prompt = f"""
        You are a professional financial advisor chatbot for PaisaPro, a personal finance management app.
        
        {user_context}
        
        Guidelines:
        1. Provide specific, actionable financial advice
        2. Give personalized suggestions based on the user's financial data when available
        3. Focus on practical tips for saving money, budgeting, and financial planning
        4. Be encouraging and supportive
        5. Keep responses concise but informative (2-3 paragraphs max)
        6. If user asks about their specific data, reference their actual numbers
        
        User Question: {message}
        
        Please provide helpful financial advice:
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful financial advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return self.get_fallback_response(message, user)
    
    def get_fallback_response(self, message, user=None):
        """Provide fallback responses when OpenAI is not available"""
        message_lower = message.lower()
        
        # Get user context for personalized responses
        user_context = ""
        if user and hasattr(user, 'account'):
            context = self.get_user_financial_context(user)
            if context:
                user_context = f"Based on your current balance of ${context['current_balance']:,.2f} and monthly income of ${context['monthly_income']:,.2f}, "
        
        # Provide specific advice based on keywords
        if any(word in message_lower for word in ['save', 'saving', 'savings']):
            return f"{user_context}Here are some savings tips: 1) Set aside 20% of your income automatically, 2) Create an emergency fund with 3-6 months of expenses, 3) Track your spending to identify areas to cut back, 4) Set specific savings goals with target amounts and dates."
        
        elif any(word in message_lower for word in ['budget', 'budgeting']):
            return f"{user_context}For effective budgeting: 1) Use the 50/30/20 rule (50% needs, 30% wants, 20% savings), 2) Track all expenses for a month to understand spending patterns, 3) Set monthly spending limits for each category, 4) Review and adjust your budget regularly."
        
        elif any(word in message_lower for word in ['invest', 'investment', 'investing']):
            return f"{user_context}Investment advice: 1) Start with low-risk options like index funds, 2) Diversify your portfolio across different asset classes, 3) Consider your risk tolerance and time horizon, 4) Don't invest money you need in the next 3-5 years."
        
        elif any(word in message_lower for word in ['expense', 'expenses', 'spending']):
            return f"{user_context}To manage expenses: 1) Categorize your spending (needs vs wants), 2) Look for recurring subscriptions you can cancel, 3) Compare prices before major purchases, 4) Set spending alerts to stay within budget."
        
        elif any(word in message_lower for word in ['debt', 'loan', 'credit']):
            return f"{user_context}Debt management: 1) Pay off high-interest debt first, 2) Consider debt consolidation if you have multiple loans, 3) Make more than minimum payments when possible, 4) Avoid taking on new debt while paying off existing ones."
        
        else:
            return f"{user_context}Here are some general financial tips: 1) Build an emergency fund, 2) Pay yourself first by saving before spending, 3) Track your net worth regularly, 4) Set specific financial goals, 5) Review your finances monthly."
    
    def get_quick_tips(self, user=None):
        """Get quick financial tips based on user's data"""
        if not user or not hasattr(user, 'account'):
            return [
                "Start by tracking your daily expenses",
                "Set aside 20% of your income for savings",
                "Create a monthly budget and stick to it",
                "Build an emergency fund with 3-6 months of expenses"
            ]
        
        account = user.account
        tips = []
        
        # Personalized tips based on user's financial situation
        if account.savings < account.monthly_income * 0.1:
            tips.append("Consider increasing your savings rate to at least 10% of your income")
        
        if account.total_expenses > account.monthly_income * 0.8:
            tips.append("Your expenses are high relative to income. Look for areas to cut back")
        
        if account.current_balance < account.monthly_income * 0.5:
            tips.append("Build a larger emergency fund for better financial security")
        
        # Add general tips
        tips.extend([
            "Review your expenses monthly to identify spending patterns",
            "Set specific financial goals with target amounts and dates",
            "Consider automating your savings transfers"
        ])
        
        return tips[:4]  # Return top 4 tips

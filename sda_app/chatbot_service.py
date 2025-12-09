import os
from django.conf import settings
import google.generativeai as genai


class FinancialChatbotService:
    def __init__(self):
        # Set Gemini API key from environment or settings
        self.api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
        self.enabled = bool(self.api_key)
        if self.enabled:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-pro (the stable v1 model)
                self.model = genai.GenerativeModel(
                    'gemini-pro',
                    generation_config={
                        "temperature": 0.9,
                        "top_p": 1,
                        "top_k": 1,
                        "max_output_tokens": 2048,
                    }
                )
                self.chat_sessions = {}  # Store chat sessions per user
            except Exception as e:
                print(f"Gemini API initialization error: {e}")
                self.enabled = False
    

    
    def generate_response(self, message, user=None):
        """Generate chatbot response with conversation context"""
        if not self.enabled:
            return self._generic_response(message)
        
        try:
            # Get or create chat session for user
            user_id = user.id if user else 'anonymous'
            if user_id not in self.chat_sessions:
                # Create new chat session with system instruction
                system_instruction = "You are PaisaPro AI, a friendly and knowledgeable financial advisor assistant. Provide practical, personalized financial advice in a conversational tone. Keep responses concise but helpful."
                
                # Add user context if available
                if user and hasattr(user, 'account'):
                    account = user.account
                    system_instruction += f"\n\nUser's Current Financial Situation:\n- Monthly Income: ${account.monthly_income}\n- Current Balance: ${account.current_balance}\n- Savings: ${account.savings}\n- Total Expenses: ${account.total_expenses}\n- Budget Limit: ${account.budget_limit}"
                
                # Start new chat
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            # Get chat session
            chat = self.chat_sessions[user_id]
            
            # Send message and get response
            response = chat.send_message(message)
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini API error: {error_msg}")
            # Clear failed session
            if user:
                self.chat_sessions.pop(user.id, None)
            
            # Return error message instead of generic response
            return f"I'm having trouble connecting to the AI service right now. Error: {error_msg}\n\nPlease check your GEMINI_API_KEY in the .env file and ensure you have API quota available."
    

    
    def _generic_response(self, message):
        """Generic helpful responses when API is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['save', 'saving', 'savings']):
            return """Here are some effective saving strategies:

1. **50/30/20 Rule**: Allocate 50% to needs, 30% to wants, and 20% to savings
2. **Automate Savings**: Set up automatic transfers to your savings account
3. **Emergency Fund**: Aim for 3-6 months of expenses
4. **Cut Unnecessary Expenses**: Review subscriptions and recurring costs
5. **High-Yield Savings**: Use accounts with better interest rates"""
        
        elif any(word in message_lower for word in ['budget', 'budgeting', 'plan']):
            return """Creating an effective budget:

1. **Track Income**: Know exactly what you earn monthly
2. **List Expenses**: Categorize into fixed and variable costs
3. **Set Limits**: Allocate specific amounts to each category
4. **Monitor Progress**: Review weekly and adjust as needed
5. **Use Tools**: Leverage apps like PaisaPro to track automatically"""
        
        elif any(word in message_lower for word in ['invest', 'investing', 'investment']):
            return """Investment basics for beginners:

1. **Start Early**: Time in the market beats timing the market
2. **Emergency Fund First**: Have 3-6 months saved before investing
3. **Diversify**: Don't put all eggs in one basket
4. **Low-Cost Index Funds**: Great for beginners
5. **Long-term Mindset**: Invest for 5+ years minimum"""
        
        elif any(word in message_lower for word in ['debt', 'loan', 'credit']):
            return """Managing debt effectively:

1. **List All Debts**: Know what you owe and interest rates
2. **Avalanche Method**: Pay high-interest debt first
3. **Minimum Payments**: Always pay at least the minimum on all debts
4. **Negotiate Rates**: Call creditors to request lower rates
5. **Avoid New Debt**: Stop using credit cards while paying off debt"""
        
        else:
            return """I'm here to help with your finances! I can provide advice on:

💰 **Saving Money** - Building emergency funds and saving strategies
📊 **Budgeting** - Creating and maintaining budgets
📈 **Investing** - Basic investment guidance
💳 **Debt Management** - Strategies to pay off debt
🎯 **Financial Goals** - Planning and achieving your goals

What would you like to know more about?"""
    
    def clear_chat_history(self, user=None):
        """Clear chat history for a user"""
        user_id = user.id if user else 'anonymous'
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]
            return True
        return False
    
    def get_quick_tips(self, user=None):
        """Get quick financial tips"""
        tips = [
            "Track every expense to understand your spending patterns",
            "Set aside 20% of your income for savings",
            "Create an emergency fund covering 3-6 months of expenses",
            "Review and adjust your budget monthly",
            "Avoid impulse purchases by waiting 24 hours before buying"
        ]
        return tips

from django.urls import path
from . import api_views

urlpatterns = [
    # CSRF Token
    path('csrf/', api_views.get_csrf_token, name='api_csrf'),
    
    # Auth endpoints
    path('signup/', api_views.signup_api, name='api_signup'),
    path('login/', api_views.login_api, name='api_login'),
    path('logout/', api_views.logout_api, name='api_logout'),
    path('verify-otp/', api_views.verify_otp_api, name='api_verify_otp'),
    path('resend-otp/', api_views.resend_otp_api, name='api_resend_otp'),
    path('forgot-password/', api_views.forgot_password_api, name='api_forgot_password'),
    path('verify-password-reset-otp/', api_views.verify_password_reset_otp_api, name='api_verify_password_reset_otp'),
    path('set-new-password/', api_views.set_new_password_api, name='api_set_new_password'),
    path('current-user/', api_views.current_user_api, name='api_current_user'),
    path('update-profile/', api_views.update_profile_api, name='api_update_profile'),
    path('verify-email-change/', api_views.verify_email_change_api, name='api_verify_email_change'),
    path('delete-account/', api_views.delete_account_api, name='api_delete_account'),
    
    # Dashboard & Account
    path('dashboard/', api_views.dashboard_api, name='api_dashboard'),
    path('account/', api_views.account_api, name='api_account'),
    path('income-setup/', api_views.income_setup_api, name='api_income_setup'),
    path('add-money/', api_views.add_money_api, name='api_add_money'),
    
    # Expenses
    path('expenses/', api_views.expenses_api, name='api_expenses'),
    path('expenses/<int:expense_id>/', api_views.expense_detail_api, name='api_expense_detail'),
    
    # Savings
    path('add-savings/', api_views.add_savings_api, name='api_add_savings'),
    path('withdraw-savings/', api_views.withdraw_savings_api, name='api_withdraw_savings'),
    
    # Budget
    path('budget/', api_views.budget_api, name='api_budget'),
    
    # Reports
    path('spending-report/', api_views.spending_report_api, name='api_spending_report'),
    
    # Chatbot
    path('chatbot/', api_views.chatbot_api, name='api_chatbot'),
    
    # Financial Insights
    path('financial-insights/', api_views.financial_insights_api, name='api_financial_insights'),
    
    # Notifications
    path('notifications/', api_views.get_notifications_api, name='api_notifications'),
    path('notifications/<int:notification_id>/read/', api_views.mark_notification_read_api, name='api_mark_notification_read'),
    path('notifications/read-all/', api_views.mark_all_notifications_read_api, name='api_mark_all_notifications_read'),
    path('notifications/clear-all/', api_views.clear_all_notifications_api, name='api_clear_all_notifications'),
]

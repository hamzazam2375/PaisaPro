from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify-otp-ajax/', views.verify_otp_ajax_view, name='verify_otp_ajax'),
    path('verify-otp/<str:email>/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/<str:email>/', views.resend_otp_view, name='resend_otp'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('income-setup/', views.income_setup_view, name='income_setup'),
    path('add-expense/', views.add_expense_view, name='add_expense'),
    path('add-salary/', views.add_money_view, name='add_money'),
    path('add-savings/', views.add_savings_view, name='add_savings'),
    path('withdraw-savings/', views.withdraw_savings_view, name='withdraw_savings'),
    path('profile-settings/', views.profile_settings_view, name='profile_settings'),
    path('email-change/', views.email_change_start_view, name='email_change_start'),
    path('email-change/verify/<str:email>/', views.email_change_verify_view, name='email_change_verify'),
    path('chatbot/', views.financial_chatbot_view, name='financial_chatbot'),
    path('chatbot-tips/', views.chatbot_tips_view, name='chatbot_tips'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]


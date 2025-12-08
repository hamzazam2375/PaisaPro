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
    path('login/', auth_views.LoginView.as_view(template_name='sda_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]


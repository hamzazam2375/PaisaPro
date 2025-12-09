from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags


class OTPService:
    """Service class for handling OTP email operations"""
    
    @staticmethod
    def send_otp_email(email, otp_code):
        """Send OTP code to user's email"""
        subject = 'PaisaPro - Email Verification Code'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #007bff;
                    margin-bottom: 30px;
                }}
                .otp-code {{
                    background-color: #f8f9fa;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: bold;
                    color: #007bff;
                    margin: 20px 0;
                    letter-spacing: 5px;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    margin-top: 30px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PaisaPro Email Verification</h1>
                </div>
                <p>Hello,</p>
                <p>Your verification code is:</p>
                <div class="otp-code">{otp_code}</div>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <div class="footer">
                    <p>© 2025 PaisaPro. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return True, 'OTP sent successfully'
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_welcome_email(email, username):
        """Send welcome email to new user"""
        subject = 'Welcome to PaisaPro!'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #28a745;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to PaisaPro, {username}!</h1>
                </div>
                <p>Your account has been successfully created.</p>
                <p>Start managing your finances with our powerful tools:</p>
                <ul>
                    <li>Track expenses by category</li>
                    <li>Set budget limits</li>
                    <li>Monitor savings goals</li>
                    <li>Get AI-powered financial insights</li>
                </ul>
                <p style="text-align: center;">
                    <a href="#" class="button">Get Started</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return True, 'Welcome email sent'
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_membership_email(email, full_name):
        """Send Paisa Pro membership email to new user"""
        subject = '🎉 Welcome to Paisa Pro Membership!'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #28a745;
                    margin-bottom: 30px;
                }}
                .badge {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 30px;
                    border-radius: 25px;
                    font-size: 18px;
                    font-weight: bold;
                    display: inline-block;
                    margin: 20px 0;
                }}
                .benefits {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .benefit-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #dee2e6;
                }}
                .benefit-item:last-child {{
                    border-bottom: none;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #28a745;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    margin-top: 30px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Congratulations {full_name}!</h1>
                    <p style="text-align: center;">
                        <span class="badge">✨ Paisa Pro Member ✨</span>
                    </p>
                </div>
                <p>Welcome to the Paisa Pro family! Your account has been successfully verified and you now have full access to all premium features.</p>
                
                <div class="benefits">
                    <h3 style="margin-top: 0; color: #007bff;">🎁 Your Membership Benefits:</h3>
                    <div class="benefit-item">
                        <strong>💰 Smart Budget Tracking</strong><br>
                        Set limits and get instant alerts when you're overspending
                    </div>
                    <div class="benefit-item">
                        <strong>📊 Detailed Reports</strong><br>
                        Visual spending reports with category breakdowns
                    </div>
                    <div class="benefit-item">
                        <strong>🤖 AI Financial Advisor</strong><br>
                        Get personalized financial advice powered by AI
                    </div>
                    <div class="benefit-item">
                        <strong>🎯 Savings Goals</strong><br>
                        Set and track your savings goals automatically
                    </div>
                    <div class="benefit-item">
                        <strong>🔍 Expense Analysis</strong><br>
                        Detect unusual expenses and spending patterns
                    </div>
                    <div class="benefit-item">
                        <strong>📧 Smart Alerts</strong><br>
                        Email notifications for important financial events
                    </div>
                </div>
                
                <p><strong>Get Started Now:</strong></p>
                <ol>
                    <li>Set your monthly income (optional but recommended)</li>
                    <li>Add your first expense to start tracking</li>
                    <li>Set a budget limit to stay on track</li>
                    <li>Chat with our AI advisor for personalized tips</li>
                </ol>
                
                <p style="text-align: center;">
                    <a href="http://localhost:3000/dashboard" class="button">Go to Dashboard</a>
                </p>
                
                <div class="footer">
                    <p>Need help? Contact us anytime!</p>
                    <p>© 2025 PaisaPro. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return True, 'Membership email sent'
        except Exception as e:
            return False, str(e)

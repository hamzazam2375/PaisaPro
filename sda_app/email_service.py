from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class OTPService:
    """Service class for handling OTP email operations"""
    
    @staticmethod
    def send_otp_email(email, otp_code):
        """Send OTP code to user's email"""
        subject = 'PaisaPro - Email Verification Code'
        
        # Create HTML email template
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
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PaisaPro</h1>
                    <h2>Email Verification</h2>
                </div>
                
                <p>Hello!</p>
                <p>Thank you for signing up with PaisaPro. To complete your registration, please use the verification code below:</p>
                
                <div class="otp-code">{otp_code}</div>
                
                <p><strong>Important:</strong></p>
                <ul>
                    <li>This code will expire in 10 minutes</li>
                    <li>Do not share this code with anyone</li>
                    <li>If you didn't request this code, please ignore this email</li>
                </ul>
                
                <div class="footer">
                    <p>This is an automated message from PaisaPro. Please do not reply to this email.</p>
                    <p>© 2024 PaisaPro. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_message = f"""
        PaisaPro - Email Verification
        
        Hello!
        
        Thank you for signing up with PaisaPro. To complete your registration, please use the verification code below:
        
        Verification Code: {otp_code}
        
        Important:
        - This code will expire in 10 minutes
        - Do not share this code with anyone
        - If you didn't request this code, please ignore this email
        
        This is an automated message from PaisaPro. Please do not reply to this email.
        
        © 2024 PaisaPro. All rights reserved.
        """
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True, "OTP sent successfully"
        except Exception as e:
            # Log the error for debugging
            print(f"Email sending error: {str(e)}")
            return False, f"Failed to send OTP: {str(e)}"
    
    @staticmethod
    def send_welcome_email(email, username):
        """Send welcome email after successful verification"""
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
                    color: #007bff;
                    margin-bottom: 30px;
                }}
                .welcome-message {{
                    background-color: #e7f3ff;
                    border-left: 4px solid #007bff;
                    padding: 20px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PaisaPro</h1>
                </div>
                
                <div class="welcome-message">
                    <h2>Welcome to PaisaPro, {username}!</h2>
                    <p>Your account has been successfully created and verified.</p>
                </div>
                
                <p>You can now:</p>
                <ul>
                    <li>Track your expenses and income</li>
                    <li>Create shopping lists and compare prices</li>
                    <li>Get monthly financial summaries</li>
                    <li>Receive AI-powered financial recommendations</li>
                </ul>
                
                <p>Start managing your finances today!</p>
                
                <p>Best regards,<br>The PaisaPro Team</p>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Welcome to PaisaPro, {username}!
        
        Your account has been successfully created and verified.
        
        You can now:
        - Track your expenses and income
        - Create shopping lists and compare prices
        - Get monthly financial summaries
        - Receive AI-powered financial recommendations
        
        Start managing your finances today!
        
        Best regards,
        The PaisaPro Team
        """
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True, "Welcome email sent successfully"
        except Exception as e:
            return False, f"Failed to send welcome email: {str(e)}"



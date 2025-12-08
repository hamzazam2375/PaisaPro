import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class WorkingEmailBackend(BaseEmailBackend):
    """
    Working email backend that bypasses SSL certificate issues
    """
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.host = host or settings.EMAIL_HOST
        self.port = port or settings.EMAIL_PORT
        self.username = username or settings.EMAIL_HOST_USER
        self.password = password or settings.EMAIL_HOST_PASSWORD
        self.use_tls = use_tls if use_tls is not None else settings.EMAIL_USE_TLS
        self.timeout = timeout or getattr(settings, 'EMAIL_TIMEOUT', None)
        self.connection = None
    
    def open(self):
        """Open connection to email server"""
        if self.connection:
            return False
        
        try:
            # Create SSL context that doesn't verify certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to server
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            self.connection.set_debuglevel(0)  # Disable debug output
            
            if self.use_tls:
                self.connection.starttls(context=context)
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except Exception as e:
            print(f"Email connection error: {str(e)}")
            if not self.fail_silently:
                raise
            return False
    
    def close(self):
        """Close connection to email server"""
        if self.connection:
            try:
                self.connection.quit()
            except:
                self.connection.close()
            self.connection = None
    
    def send_messages(self, email_messages):
        """Send email messages"""
        if not email_messages:
            return 0
        
        if not self.open():
            return 0
        
        sent = 0
        try:
            for message in email_messages:
                sent += self._send_message(message)
        except Exception as e:
            print(f"Email sending error: {str(e)}")
            if not self.fail_silently:
                raise
        finally:
            self.close()
        
        return sent
    
    def _send_message(self, message):
        """Send a single email message"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = message.from_email
            msg['To'] = ', '.join(message.to)
            msg['Subject'] = message.subject
            
            # Add text content
            if message.body:
                text_part = MIMEText(message.body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if hasattr(message, 'alternatives') and message.alternatives:
                for content, mimetype in message.alternatives:
                    if mimetype == 'text/html':
                        html_part = MIMEText(content, 'html', 'utf-8')
                        msg.attach(html_part)
            
            # Send message
            self.connection.send_message(msg)
            return 1
            
        except Exception as e:
            print(f"Message sending error: {str(e)}")
            if not self.fail_silently:
                raise
            return 0

import ssl
import socket
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class CustomSMTPEmailBackend(EmailBackend):
    """
    Custom SMTP backend that handles SSL certificate issues on Windows
    """
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        super().__init__(host, port, username, password, use_tls, fail_silently, 
                        use_ssl, timeout, ssl_keyfile, ssl_certfile, **kwargs)
        self.local_hostname = None
    
    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a new
        connection was required (True or False) or None if an exception occurred.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        
        try:
            # If local_hostname is not specified, socket.getfqdn() gets the
            # canonical name, which is more likely to be correct for sending
            # mail than the hostname returned by socket.gethostname().
            if self.local_hostname is None:
                self.local_hostname = socket.getfqdn()
            
            if self.host == 'smtp.gmail.com':
                # Create SSL context for Gmail
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # Use the custom SSL context
                self.connection = self.connection_class(
                    self.host, self.port, 
                    local_hostname=self.local_hostname,
                    timeout=self.timeout,
                    ssl_context=context
                )
            else:
                # Use default connection for other SMTP servers
                self.connection = self.connection_class(
                    self.host, self.port, 
                    local_hostname=self.local_hostname,
                    timeout=self.timeout
                )
            
            if self.use_tls:
                self.connection.starttls()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"SMTP Connection Error: {str(e)}")
            if not self.fail_silently:
                raise
            return False

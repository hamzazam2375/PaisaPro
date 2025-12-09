<<<<<<< Updated upstream
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SDA_Project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
=======
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    
    # Sets the settings module that Django should use
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SDA_Project.settings')

    try:
        # Imports Django's command-line executor
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Error if Django isn't installed or environment isn't activated
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Runs whatever command you typed in terminal (runserver, migrate, etc.)
    execute_from_command_line(sys.argv)


# Runs the main() function only if this file is executed directly
if __name__ == '__main__':
    main()
>>>>>>> Stashed changes

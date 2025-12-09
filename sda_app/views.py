# Minimal views for Django admin compatibility
# Main application now uses React frontend with REST API

from django.http import HttpResponse

def health_check(request):
    """Health check endpoint"""
    return HttpResponse("OK")

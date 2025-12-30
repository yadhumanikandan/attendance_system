"""
Context processors for the attendance app.
These make data available to all templates.
"""

from .models import EarlyLeaveRequest


def pending_requests_processor(request):
    """
    Add pending on-duty requests count and list to all templates.
    Only for superuser.
    """
    if request.user.is_authenticated and request.user.is_superuser:
        pending_requests = EarlyLeaveRequest.objects.filter(
            status='pending'
        ).order_by('-request_date', '-id')
        return {
            'nav_pending_requests': pending_requests,
            'nav_pending_count': pending_requests.count()
        }
    return {
        'nav_pending_requests': [],
        'nav_pending_count': 0
    }

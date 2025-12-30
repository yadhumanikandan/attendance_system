"""
Leave management views for admin.
Handles leave request viewing, approval, and rejection.
"""

import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test

from ..models import LeaveRequest, Employee


def superuser_required(user):
    return user.is_superuser


@login_required
@user_passes_test(superuser_required)
def leave_management(request):
    """Admin page to view and manage leave requests."""
    # Get filter parameters
    status_filter = request.GET.get('status', 'pending')
    
    # Get all leave requests, filtered by status if specified
    if status_filter == 'all':
        leave_requests = LeaveRequest.objects.all().select_related('employee')
    else:
        leave_requests = LeaveRequest.objects.filter(status=status_filter).select_related('employee')
    
    # Get counts for tab badges
    pending_count = LeaveRequest.objects.filter(status='pending').count()
    approved_count = LeaveRequest.objects.filter(status='approved').count()
    rejected_count = LeaveRequest.objects.filter(status='rejected').count()
    
    context = {
        'leave_requests': leave_requests,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'attendance/leave_management.html', context)


@login_required
@user_passes_test(superuser_required)
@require_http_methods(["POST"])
def approve_leave(request, leave_id):
    """Approve a leave request with optional day adjustment."""
    try:
        leave_request = LeaveRequest.objects.get(id=leave_id)
        
        if leave_request.status != 'pending':
            return JsonResponse({'success': False, 'error': 'This request has already been processed'})
        
        # Get approved days and dates from request
        approved_days = request.POST.get('approved_days')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        admin_notes = request.POST.get('admin_notes', '').strip()
        
        # Update dates if provided
        if start_date_str and end_date_str:
            try:
                new_start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                new_end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                # Basic validation: start date should not be after end date
                if new_start_date <= new_end_date:
                    leave_request.start_date = new_start_date
                    leave_request.end_date = new_end_date
            except ValueError:
                pass # Ignore invalid date formats and keep original dates

        try:
            approved_days = int(approved_days) if approved_days else leave_request.requested_days
        except ValueError:
            approved_days = leave_request.requested_days
        
        # Validate approved days against the (possibly new) duration
        # We allow approved_days to be less than duration (partial pay), but should we limit it?
        # The existing logic limits it to requested_days. 
        # If we changed dates, the "requested_days" context changes.
        # Let's verify against the *current* duration of the request (after date update).
        
        current_duration = (leave_request.end_date - leave_request.start_date).days + 1
        if approved_days < 1: 
            approved_days = 1
            
        # If approved days > duration, cap it at duration
        if approved_days > current_duration:
            approved_days = current_duration
        
        leave_request.status = 'approved'
        leave_request.approved_days = approved_days
        leave_request.admin_notes = admin_notes
        leave_request.reviewed_at = datetime.datetime.now()
        leave_request.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Leave approved for {approved_days} day(s)'
        })
        
    except LeaveRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Leave request not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(superuser_required)
@require_http_methods(["POST"])
def reject_leave(request, leave_id):
    """Reject a leave request."""
    try:
        leave_request = LeaveRequest.objects.get(id=leave_id)
        
        if leave_request.status != 'pending':
            return JsonResponse({'success': False, 'error': 'This request has already been processed'})
        
        admin_notes = request.POST.get('admin_notes', '').strip()
        
        if not admin_notes:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection'})
        
        leave_request.status = 'rejected'
        leave_request.admin_notes = admin_notes
        leave_request.reviewed_at = datetime.datetime.now()
        leave_request.save()
        
        return JsonResponse({'success': True, 'message': 'Leave request rejected'})
        
    except LeaveRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Leave request not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

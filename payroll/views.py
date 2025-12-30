"""
Payroll calculation views.
"""

import json
import datetime
import calendar
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum

from attendance.models import Employee, MonthlySummary, Holiday, LeaveRequest
from .models import PayrollAdjustment


def superuser_required(user):
    return user.is_superuser


@login_required
@user_passes_test(superuser_required, login_url='/report/')
def payroll_dashboard(request):
    """
    Payroll dashboard showing Admin and Sales sections.
    
    Admin Payroll Formula: 
    Base = (monthly_salary / 30) * working_days
    Net = Base + Incentives - Reductions
    """
    now = datetime.datetime.now()
    
    try:
        selected_month = int(request.GET.get('month', now.month))
        selected_year = int(request.GET.get('year', now.year))
    except ValueError:
        selected_month = now.month
        selected_year = now.year
    
    # Get number of days in month and count holidays
    _, days_in_month = calendar.monthrange(selected_year, selected_month)
    
    # Count Sundays
    sundays = 0
    for day in range(1, days_in_month + 1):
        if datetime.date(selected_year, selected_month, day).weekday() == 6:
            sundays += 1
    
    # Get holidays
    holidays = Holiday.objects.filter(
        date__year=selected_year,
        date__month=selected_month
    ).count()
    
    total_holidays = sundays + holidays
    
    # Get Admin employees with their monthly summaries
    admin_employees = Employee.objects.filter(
        department='Admin',
        is_active=True
    ).order_by('name')
    
    admin_payroll_data = []
    total_admin_payroll = 0
    total_incentives = 0
    total_reductions = 0
    
    for emp in admin_employees:
        # Get monthly summary
        summary = MonthlySummary.objects.filter(
            employee=emp,
            year=selected_year,
            month=selected_month
        ).first()
        
        # Calculate working days
        if summary:
            full_days = summary.working_days - (summary.half_days or 0)
            half_days = summary.half_days or 0
            working_days = full_days + (half_days * 0.5) + total_holidays
        else:
            full_days = 0
            half_days = 0
            working_days = total_holidays  # Only holidays if no attendance data
        
        # Get salary (default to 0 if not set)
        salary = float(emp.salary) if emp.salary else 0.0
        
        # Get approved paid leave days for this employee this month
        approved_leaves = LeaveRequest.objects.filter(
            employee=emp,
            status='approved',
            start_date__year=selected_year,
            start_date__month=selected_month
        )
        paid_leave_days = sum(leave.get_effective_days() for leave in approved_leaves)
        
        # Calculate base payroll: salary / 30 * (working_days + paid_leave_days)
        daily_rate = salary / 30 if salary > 0 else 0.0
        total_working_days = working_days + paid_leave_days
        base_payroll = daily_rate * total_working_days
        
        # Get adjustments for this employee this month
        adjustments = PayrollAdjustment.objects.filter(
            employee=emp,
            year=selected_year,
            month=selected_month
        )
        
        incentives = float(adjustments.filter(adjustment_type='incentive').aggregate(
            total=Sum('amount'))['total'] or 0)
        reductions = float(adjustments.filter(adjustment_type='reduction').aggregate(
            total=Sum('amount'))['total'] or 0)
        
        # Calculate net payroll
        net_payroll = base_payroll + incentives - reductions
        
        admin_payroll_data.append({
            'employee': emp,
            'salary': salary,
            'working_days': total_working_days,
            'daily_rate': round(daily_rate, 2),
            'base_payroll': round(base_payroll, 2),
            'incentives': round(incentives, 2),
            'reductions': round(reductions, 2),
            'net_payroll': round(net_payroll, 2),
            'full_days': full_days,
            'half_days': half_days,
            'holidays': total_holidays,
            'paid_leave_days': paid_leave_days,
        })
        
        total_admin_payroll += net_payroll
        total_incentives += incentives
        total_reductions += reductions
    
    # Month names for dropdown
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    context = {
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': month_names[selected_month],
        'months': [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        'years': range(2020, 2036),
        'admin_payroll_data': admin_payroll_data,
        'total_admin_payroll': round(total_admin_payroll, 2),
        'total_incentives': round(total_incentives, 2),
        'total_reductions': round(total_reductions, 2),
        'total_holidays': total_holidays,
    }
    
    return render(request, 'payroll/dashboard.html', context)


# ============================================
# API Endpoints for Adjustments
# ============================================

@login_required
@user_passes_test(superuser_required, login_url='/report/')
def get_adjustments(request, employee_id):
    """Get all adjustments for an employee for a specific month."""
    try:
        year = int(request.GET.get('year', datetime.datetime.now().year))
        month = int(request.GET.get('month', datetime.datetime.now().month))
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid year/month'})
    
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'})
    
    adjustments = PayrollAdjustment.objects.filter(
        employee=employee,
        year=year,
        month=month
    )
    
    data = [{
        'id': adj.id,
        'type': adj.adjustment_type,
        'amount': float(adj.amount),
        'reason': adj.reason,
        'created_at': adj.created_at.strftime('%Y-%m-%d %H:%M')
    } for adj in adjustments]
    
    return JsonResponse({
        'success': True,
        'employee_name': employee.name,
        'adjustments': data
    })


@login_required
@user_passes_test(superuser_required, login_url='/report/')
@require_http_methods(["POST"])
def add_adjustment(request):
    """Add a new adjustment for an employee."""
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        year = data.get('year')
        month = data.get('month')
        adjustment_type = data.get('type')
        amount = data.get('amount')
        reason = data.get('reason', '')
        
        if not all([employee_id, year, month, adjustment_type, amount]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        employee = Employee.objects.get(id=employee_id)
        
        adjustment = PayrollAdjustment.objects.create(
            employee=employee,
            year=year,
            month=month,
            adjustment_type=adjustment_type,
            amount=Decimal(str(amount)),
            reason=reason
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Adjustment added successfully',
            'adjustment': {
                'id': adjustment.id,
                'type': adjustment.adjustment_type,
                'amount': float(adjustment.amount),
                'reason': adjustment.reason
            }
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'})
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})


@login_required
@user_passes_test(superuser_required, login_url='/report/')
@require_http_methods(["POST"])
def delete_adjustment(request, adjustment_id):
    """Delete an adjustment."""
    try:
        adjustment = PayrollAdjustment.objects.get(id=adjustment_id)
        adjustment.delete()
        return JsonResponse({'success': True, 'message': 'Adjustment deleted'})
    except PayrollAdjustment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Adjustment not found'})

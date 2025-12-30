"""
Employee management views for admin users.
Custom interface for managing all employees without Django admin.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password

from ..models import Employee, RemoteEmployee
from .utils import superuser_required


@login_required
@user_passes_test(superuser_required, login_url='/report/')
def employee_management(request):
    """Display all employees (in-house and remote) in a unified management page."""
    # Get all in-house employees
    inhouse_employees = Employee.objects.all().order_by('name')
    
    # Get all remote employees
    remote_employees = RemoteEmployee.objects.all().order_by('name')
    
    # Combine into unified list with type indicator
    all_employees = []
    
    for emp in inhouse_employees:
        all_employees.append({
            'id': emp.id,
            'type': 'inhouse',
            'identifier': emp.person_id,
            'name': emp.name,
            'email': emp.email or '',
            'phone': emp.phone or '',
            'department': emp.department or '',
            'location': emp.location or '',
            'team': emp.team or '',
            'is_active': emp.is_active,
            'salary': float(emp.salary) if emp.salary else None,
            'joining_date': emp.joining_date.strftime('%Y-%m-%d') if emp.joining_date else '',
            'leaving_date': emp.leaving_date.strftime('%Y-%m-%d') if emp.leaving_date else '',
        })
    
    for emp in remote_employees:
        salary = getattr(emp, 'salary', None)
        all_employees.append({
            'id': emp.id,
            'type': 'remote',
            'identifier': emp.extension_id,
            'name': emp.name,
            'email': emp.email or '',
            'phone': emp.phone or '',
            'department': emp.department or '',
            'location': emp.location or '',
            'team': emp.team or '',
            'is_active': emp.is_active,
            'salary': float(salary) if salary else None,
            'joining_date': emp.joining_date.strftime('%Y-%m-%d') if emp.joining_date else '',
            'leaving_date': emp.leaving_date.strftime('%Y-%m-%d') if emp.leaving_date else '',
        })
    
    # Sort by name
    all_employees.sort(key=lambda x: x['name'].lower())
    
    # Get unique values for filters
    departments = sorted(set(e['department'] for e in all_employees if e['department']))
    locations = sorted(set(e['location'] for e in all_employees if e['location']))
    teams = sorted(set(e['team'] for e in all_employees if e['team']))
    
    context = {
        'employees': all_employees,
        'departments': departments,
        'locations': locations,
        'teams': teams,
        'total_count': len(all_employees),
        'inhouse_count': len(inhouse_employees),
        'remote_count': len(remote_employees),
    }
    
    return render(request, 'attendance/employee_management.html', context)


@login_required
@user_passes_test(superuser_required, login_url='/report/')
def update_employee(request):
    """API endpoint to update employee data."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    try:
        data = json.loads(request.body)
        employee_id = data.get('id')
        employee_type = data.get('type')
        
        if not employee_id or not employee_type:
            return JsonResponse({'success': False, 'error': 'Missing id or type'})
        
        # Get the appropriate employee model
        if employee_type == 'inhouse':
            try:
                emp = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Employee not found'})
        else:
            try:
                emp = RemoteEmployee.objects.get(id=employee_id)
            except RemoteEmployee.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Remote employee not found'})
        
        # Update fields
        if 'name' in data:
            emp.name = data['name']
        if 'email' in data:
            emp.email = data['email'] or None
        if 'phone' in data:
            emp.phone = data['phone'] or None
        if 'department' in data:
            emp.department = data['department'] or None
        if 'location' in data:
            emp.location = data['location'] or None
        if 'team' in data:
            emp.team = data['team'] or None
        if 'is_active' in data:
            emp.is_active = data['is_active']
        if 'salary' in data:
            emp.salary = data['salary']
        if 'joining_date' in data:
            emp.joining_date = data['joining_date'] or None
        if 'leaving_date' in data:
            emp.leaving_date = data['leaving_date'] or None
        if 'portal_password' in data and data['portal_password']:
            emp.portal_password = make_password(data['portal_password'])
        
        emp.save()
        
        return JsonResponse({'success': True, 'message': 'Employee updated successfully'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(superuser_required, login_url='/report/')
def bulk_update_employees(request):
    """API endpoint to bulk update employee fields."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    try:
        data = json.loads(request.body)
        employee_ids = data.get('employees', [])  # List of {id, type}
        updates = data.get('updates', {})  # Fields to update
        
        if not employee_ids:
            return JsonResponse({'success': False, 'error': 'No employees selected'})
        
        updated_count = 0
        
        for emp_info in employee_ids:
            emp_id = emp_info.get('id')
            emp_type = emp_info.get('type')
            
            try:
                if emp_type == 'inhouse':
                    emp = Employee.objects.get(id=emp_id)
                else:
                    emp = RemoteEmployee.objects.get(id=emp_id)
                
                # Apply updates
                for field, value in updates.items():
                    if field in ['department', 'location', 'team']:
                        setattr(emp, field, value or None)
                    elif field == 'is_active':
                        emp.is_active = value
                
                emp.save()
                updated_count += 1
                
            except (Employee.DoesNotExist, RemoteEmployee.DoesNotExist):
                continue
        
        return JsonResponse({
            'success': True, 
            'message': f'Updated {updated_count} employees'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

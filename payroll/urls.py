from django.urls import path
from . import views

urlpatterns = [
    path('', views.payroll_dashboard, name='payroll_dashboard'),
    # API endpoints for adjustments
    path('api/adjustments/<int:employee_id>/', views.get_adjustments, name='get_adjustments'),
    path('api/adjustments/add/', views.add_adjustment, name='add_adjustment'),
    path('api/adjustments/delete/<int:adjustment_id>/', views.delete_adjustment, name='delete_adjustment'),
]

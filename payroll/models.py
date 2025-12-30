"""
Payroll models for salary adjustments.
"""

from django.db import models
from attendance.models import Employee


class PayrollAdjustment(models.Model):
    """
    Monthly adjustments (incentives/reductions) for employee payroll.
    Each adjustment is per-employee, per-month with a reason.
    """
    ADJUSTMENT_TYPES = [
        ('incentive', 'Incentive'),
        ('reduction', 'Reduction'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='payroll_adjustments'
    )
    year = models.IntegerField()
    month = models.IntegerField(help_text="1-12")
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(help_text="Reason for the adjustment")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'year', 'month']),
        ]
    
    def __str__(self):
        sign = '+' if self.adjustment_type == 'incentive' else '-'
        return f"{self.employee.name} {self.year}/{self.month}: {sign}{self.amount}"

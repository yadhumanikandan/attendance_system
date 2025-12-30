from django.contrib import admin
from .models import PayrollAdjustment


@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'year', 'month', 'adjustment_type', 'amount', 'reason', 'created_at')
    list_filter = ('adjustment_type', 'year', 'month')
    search_fields = ('employee__name', 'reason')
    ordering = ('-year', '-month', '-created_at')

from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model."""
    
    list_display = [
        'customer_id',
        'full_name',
        'age',
        'monthly_salary',
        'approved_limit',
        'current_debt',
        'credit_utilization_percent',
    ]
    list_filter = ['age', 'monthly_salary']
    search_fields = ['customer_id', 'first_name', 'last_name', 'phone_number']
    readonly_fields = ['current_debt', 'created_at', 'updated_at', 'credit_utilization_percent']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer_id', 'first_name', 'last_name', 'age', 'phone_number')
        }),
        ('Financial Information', {
            'fields': ('monthly_salary', 'approved_limit', 'current_debt', 'credit_utilization_percent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def credit_utilization_percent(self, obj):
        """Display credit utilization as percentage."""
        return f"{obj.credit_utilization * 100:.2f}%"
    credit_utilization_percent.short_description = 'Credit Utilization'
    
    def full_name(self, obj):
        """Display customer's full name."""
        return obj.full_name
    full_name.short_description = 'Name'
    full_name.admin_order_field = 'first_name'


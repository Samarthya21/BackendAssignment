from django.contrib import admin
from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin interface for Loan model."""
    
    list_display = [
        'loan_id',
        'customer_link',
        'loan_amount',
        'tenure',
        'interest_rate',
        'monthly_repayment',
        'payment_status',
        'date_of_approval',
        'is_active',
    ]
    list_filter = [
        'date_of_approval',
        'tenure',
        'interest_rate',
        'emis_paid_on_time',
    ]
    search_fields = [
        'loan_id',
        'customer__customer_id',
        'customer__first_name',
        'customer__last_name',
    ]
    readonly_fields = [
        'remaining_emis',
        'remaining_amount',
        'payment_percentage_display',
        'is_current',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['customer']
    date_hierarchy = 'date_of_approval'
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('loan_id', 'customer', 'loan_amount', 'tenure')
        }),
        ('Financial Details', {
            'fields': ('interest_rate', 'monthly_repayment')
        }),
        ('Repayment Status', {
            'fields': (
                'emis_paid_on_time',
                'remaining_emis',
                'remaining_amount',
                'payment_percentage_display',
                'is_current',
            )
        }),
        ('Dates', {
            'fields': ('date_of_approval', 'end_date', 'created_at', 'updated_at'),
        }),
    )
    
    def customer_link(self, obj):
        """Display clickable customer name."""
        return f"{obj.customer.full_name} (ID: {obj.customer.customer_id})"
    customer_link.short_description = 'Customer'
    customer_link.admin_order_field = 'customer__first_name'
    
    def payment_status(self, obj):
        """Display payment completion percentage."""
        return f"{obj.payment_percentage:.1f}%"
    payment_status.short_description = 'Paid'
    payment_status.admin_order_field = 'emis_paid_on_time'
    
    def payment_percentage_display(self, obj):
        """Display detailed payment percentage."""
        return f"{obj.payment_percentage:.2f}% ({obj.emis_paid_on_time}/{obj.tenure} EMIs)"
    payment_percentage_display.short_description = 'Payment Progress'


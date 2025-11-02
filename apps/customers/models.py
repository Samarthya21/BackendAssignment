from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Customer(models.Model):
    """
    Customer model representing credit applicants and existing customers.
    
    Fields map directly to the customerData.csv structure.
    The approved_limit is calculated as 36 * monthly_salary during ingestion.
    Current debt is calculated from active loans.
    """
    customer_id = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="External customer ID from CSV data"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(120)]
    )
    phone_number = models.CharField(max_length=15, blank=True)
    monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    approved_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Approved credit limit (36 * monthly_salary)"
    )
    current_debt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Sum of all outstanding loan EMIs"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['customer_id']
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.customer_id})"
    
    def update_current_debt(self):
        """
        Update current debt from all active loans.
        Current debt = sum of (monthly_repayment * remaining EMIs) for all active loans.
        """
        from apps.loans.models import Loan
        
        active_loans = Loan.objects.filter(
            customer=self,
            emis_paid_on_time__lt=models.F('tenure')
        )
        
        total_debt = sum(
            loan.monthly_repayment * (loan.tenure - loan.emis_paid_on_time)
            for loan in active_loans
        )
        
        self.current_debt = total_debt
        self.save(update_fields=['current_debt', 'updated_at'])
        return self.current_debt
    
    @property
    def full_name(self):
        """Return customer's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def credit_utilization(self):
        """Calculate credit utilization ratio (current_debt / approved_limit)."""
        if self.approved_limit == 0:
            return 0
        return float(self.current_debt / self.approved_limit)


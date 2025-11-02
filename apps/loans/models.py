from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Loan(models.Model):
    """
    Loan model representing approved loans for customers.
    
    Fields map directly to the loanData.csv structure.
    Tracks loan details, repayment status, and payment history.
    """
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='loans',
        db_index=True
    )
    loan_id = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="External loan ID from CSV data"
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tenure = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text="Loan tenure in months"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Annual interest rate percentage"
    )
    monthly_repayment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly EMI amount"
    )
    emis_paid_on_time = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of EMIs paid on time"
    )
    date_of_approval = models.DateField(
        help_text="Loan approval date"
    )
    end_date = models.DateField(
        help_text="Expected loan end date"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'loans'
        ordering = ['-date_of_approval']
        indexes = [
            models.Index(fields=['loan_id']),
            models.Index(fields=['customer', '-date_of_approval']),
            models.Index(fields=['date_of_approval']),
        ]
    
    def __str__(self):
        return f"Loan {self.loan_id} - {self.customer.full_name}"
    
    @property
    def is_active(self):
        """Check if loan is still active (not fully paid)."""
        return self.emis_paid_on_time < self.tenure
    
    @property
    def remaining_emis(self):
        """Calculate remaining EMIs."""
        return max(0, self.tenure - self.emis_paid_on_time)
    
    @property
    def remaining_amount(self):
        """Calculate remaining loan amount to be paid."""
        return self.monthly_repayment * self.remaining_emis
    
    @property
    def payment_percentage(self):
        """Calculate percentage of loan paid."""
        if self.tenure == 0:
            return 0
        return (self.emis_paid_on_time / self.tenure) * 100
    
    @property
    def is_current(self):
        """
        Check if loan payments are current (not overdue).
        A loan is current if emis_paid >= months since approval.
        """
        if not self.date_of_approval:
            return True
        
        months_since_approval = (
            (timezone.now().date().year - self.date_of_approval.year) * 12 +
            (timezone.now().date().month - self.date_of_approval.month)
        )
        
        return self.emis_paid_on_time >= months_since_approval
    
    def save(self, *args, **kwargs):
        """
        Override save to update customer's current debt after loan changes.
        """
        super().save(*args, **kwargs)
        # Update customer's debt after loan is saved
        if self.customer_id:
            self.customer.update_current_debt()


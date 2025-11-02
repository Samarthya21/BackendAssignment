"""
Serializers for Loan API endpoints.
"""
from rest_framework import serializers
from decimal import Decimal
from datetime import datetime, timedelta

from apps.loans.models import Loan
from apps.customers.models import Customer
from apps.core.credit_scoring import CreditScorer
from apps.core.validators import (
    validate_loan_amount,
    validate_tenure,
    validate_interest_rate
)


class LoanEligibilityRequestSerializer(serializers.Serializer):
    """
    Request serializer for loan eligibility check.
    POST /api/check-eligibility/
    """
    customer_id = serializers.IntegerField(min_value=1)
    loan_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('100')
    )
    tenure = serializers.IntegerField(min_value=1, max_value=600)
    
    def validate_customer_id(self, value):
        """Check if customer exists."""
        try:
            Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        return value
    
    def validate_loan_amount(self, value):
        """Validate loan amount."""
        validate_loan_amount(value)
        return value
    
    def validate_tenure(self, value):
        """Validate tenure."""
        validate_tenure(value)
        return value
    
    def validate_interest_rate(self, value):
        """Validate interest rate."""
        validate_interest_rate(value)
        return value


class LoanEligibilityResponseSerializer(serializers.Serializer):
    """
    Response serializer for loan eligibility check.
    """
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField(source='approved')
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )


class CreateLoanRequestSerializer(serializers.Serializer):
    """
    Request serializer for loan creation.
    POST /api/create-loan/
    """
    customer_id = serializers.IntegerField(min_value=1)
    loan_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('100')
    )
    tenure = serializers.IntegerField(min_value=1, max_value=600)
    
    def validate_customer_id(self, value):
        """Check if customer exists."""
        try:
            Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        return value
    
    def validate_loan_amount(self, value):
        """Validate loan amount."""
        validate_loan_amount(value)
        return value
    
    def validate_tenure(self, value):
        """Validate tenure."""
        validate_tenure(value)
        return value
    
    def validate_interest_rate(self, value):
        """Validate interest rate."""
        validate_interest_rate(value)
        return value
    
    def validate(self, attrs):
        """Check eligibility before allowing loan creation."""
        customer = Customer.objects.get(customer_id=attrs['customer_id'])
        scorer = CreditScorer(customer)
        
        eligibility = scorer.evaluate_loan_eligibility(
            loan_amount=attrs['loan_amount'],
            tenure=attrs['tenure'],
            interest_rate=attrs['interest_rate']
        )
        
        if not eligibility['approved']:
            raise serializers.ValidationError({
                'non_field_errors': [eligibility['message']]
            })
        
        # Store corrected interest rate for loan creation
        attrs['_corrected_interest_rate'] = eligibility['corrected_interest_rate']
        attrs['_monthly_installment'] = eligibility['monthly_installment']
        
        return attrs
    
    def create(self, validated_data):
        """Create loan with eligibility-approved terms."""
        customer = Customer.objects.get(customer_id=validated_data['customer_id'])
        
        # Get the next loan_id
        last_loan = Loan.objects.order_by('-loan_id').first()
        next_loan_id = (last_loan.loan_id + 1) if last_loan else 1
        
        # Calculate dates
        date_of_approval = datetime.now().date()
        end_date = date_of_approval + timedelta(days=validated_data['tenure'] * 30)
        
        loan = Loan.objects.create(
            customer=customer,
            loan_id=next_loan_id,
            loan_amount=validated_data['loan_amount'],
            tenure=validated_data['tenure'],
            interest_rate=validated_data['_corrected_interest_rate'],
            monthly_repayment=validated_data['_monthly_installment'],
            emis_paid_on_time=0,
            date_of_approval=date_of_approval,
            end_date=end_date
        )
        
        return loan


class CreateLoanResponseSerializer(serializers.Serializer):
    """
    Response serializer for loan creation.
    """
    loan_id = serializers.IntegerField()
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField(default=True)
    message = serializers.CharField()
    monthly_installment = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )


class LoanDetailSerializer(serializers.ModelSerializer):
    """
    Detailed loan information serializer.
    Used for view-loan and view-loans endpoints.
    """
    customer = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'customer',
            'loan_amount',
            'interest_rate',
            'monthly_repayment',
            'tenure',
            'emis_paid_on_time',
            'date_of_approval',
            'end_date'
        ]
        read_only_fields = fields
    
    def get_customer(self, obj):
        """Return customer details in nested format."""
        return {
            'customer_id': obj.customer.customer_id,
            'first_name': obj.customer.first_name,
            'last_name': obj.customer.last_name,
            'phone_number': obj.customer.phone_number,
            'age': obj.customer.age
        }


class CustomerLoansSerializer(serializers.Serializer):
    """
    Serializer for customer's all loans view.
    GET /api/view-loans/<customer_id>/
    """
    customer_id = serializers.IntegerField()
    loans = LoanDetailSerializer(many=True)

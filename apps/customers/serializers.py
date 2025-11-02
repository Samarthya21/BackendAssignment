"""
Serializers for Customer API endpoints.
"""
from rest_framework import serializers
from decimal import Decimal

from apps.customers.models import Customer
from apps.core.utils import calculate_approved_limit
from apps.core.validators import validate_phone_number, validate_age


class CustomerRegistrationSerializer(serializers.Serializer):
    """
    Serializer for customer registration endpoint.
    POST /api/register/
    """
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=18, max_value=120)
    monthly_income = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    
    def validate_age(self, value):
        """Validate age using custom validator."""
        validate_age(value)
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if value:
            validate_phone_number(value)
        return value
    
    def validate(self, attrs):
        """Check for duplicate phone number."""
        phone = attrs.get('phone_number', '')
        if phone and Customer.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError({
                'phone_number': 'A customer with this phone number already exists'
            })
        return attrs
    
    def create(self, validated_data):
        """Create customer with auto-calculated approved limit."""
        monthly_income = validated_data['monthly_income']
        
        # Calculate approved limit (36 * monthly salary, rounded to nearest lakh)
        approved_limit = calculate_approved_limit(monthly_income)
        # Round to nearest lakh (100,000)
        approved_limit = round(approved_limit / 100000) * 100000
        
        # Get the next customer_id
        last_customer = Customer.objects.order_by('-customer_id').first()
        next_customer_id = (last_customer.customer_id + 1) if last_customer else 1
        
        customer = Customer.objects.create(
            customer_id=next_customer_id,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            age=validated_data['age'],
            phone_number=validated_data.get('phone_number', ''),
            monthly_salary=monthly_income,
            approved_limit=approved_limit,
            current_debt=Decimal('0')
        )
        
        return customer


class CustomerRegistrationResponseSerializer(serializers.ModelSerializer):
    """
    Response serializer for customer registration.
    """
    name = serializers.CharField(source='full_name', read_only=True)
    monthly_income = serializers.DecimalField(
        source='monthly_salary',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Customer
        fields = [
            'customer_id',
            'name',
            'age',
            'monthly_income',
            'approved_limit',
            'phone_number'
        ]
        read_only_fields = fields


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Detailed customer information serializer.
    """
    name = serializers.CharField(source='full_name', read_only=True)
    monthly_salary = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Customer
        fields = [
            'customer_id',
            'name',
            'first_name',
            'last_name',
            'age',
            'phone_number',
            'monthly_salary',
            'approved_limit',
            'current_debt'
        ]
        read_only_fields = fields

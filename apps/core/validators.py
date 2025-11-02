"""
Custom validators for the Credit Approval System.
Implements business rules and validation logic.
"""
from decimal import Decimal
from typing import Tuple

from django.core.exceptions import ValidationError


def validate_age(age: int) -> None:
    """
    Validate customer age.
    
    Args:
        age: Customer age
    
    Raises:
        ValidationError: If age is invalid
    """
    if age < 18:
        raise ValidationError("Customer must be at least 18 years old")
    if age > 120:
        raise ValidationError("Invalid age value")


def validate_phone_number(phone: str) -> None:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number string
    
    Raises:
        ValidationError: If phone number is invalid
    """
    if not phone:
        return
    
    # Remove common separators
    cleaned = phone.replace('-', '').replace(' ', '').replace('+', '')
    
    if not cleaned.isdigit():
        raise ValidationError("Phone number must contain only digits")
    
    if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValidationError("Phone number must be between 10 and 15 digits")


def validate_loan_amount(
    amount: Decimal,
    min_amount: Decimal = Decimal('10000'),
    max_amount: Decimal = Decimal('10000000')
) -> None:
    """
    Validate loan amount.
    
    Args:
        amount: Loan amount to validate
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount
    
    Raises:
        ValidationError: If amount is invalid
    """
    if amount < min_amount:
        raise ValidationError(f"Loan amount must be at least ₹{min_amount:,.2f}")
    
    if amount > max_amount:
        raise ValidationError(f"Loan amount cannot exceed ₹{max_amount:,.2f}")


def validate_tenure(tenure: int) -> None:
    """
    Validate loan tenure.
    
    Args:
        tenure: Loan tenure in months
    
    Raises:
        ValidationError: If tenure is invalid
    """
    if tenure < 1:
        raise ValidationError("Loan tenure must be at least 1 month")
    
    if tenure > 600:
        raise ValidationError("Loan tenure cannot exceed 600 months (50 years)")


def validate_interest_rate(rate: Decimal) -> None:
    """
    Validate interest rate.
    
    Args:
        rate: Annual interest rate percentage
    
    Raises:
        ValidationError: If rate is invalid
    """
    if rate < 0:
        raise ValidationError("Interest rate cannot be negative")
    
    if rate > 100:
        raise ValidationError("Interest rate cannot exceed 100%")


def validate_emi_to_salary_ratio(
    monthly_emi: Decimal,
    monthly_salary: Decimal,
    max_ratio: float = 0.5
) -> Tuple[bool, float]:
    """
    Validate EMI to salary ratio.
    
    Per assignment requirements, sum of all current EMIs should not exceed
    50% of monthly salary.
    
    Args:
        monthly_emi: Total monthly EMI (all loans)
        monthly_salary: Customer's monthly salary
        max_ratio: Maximum allowed ratio (default: 0.5 = 50%)
    
    Returns:
        Tuple of (is_valid, actual_ratio)
    """
    if monthly_salary == 0:
        return False, float('inf')
    
    ratio = float(monthly_emi / monthly_salary)
    is_valid = ratio <= max_ratio
    
    return is_valid, ratio

"""
Core utilities for the Credit Approval System.
Contains helper functions, validators, and business logic utilities.
"""
from decimal import Decimal
from typing import Dict, Any


def calculate_emi(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int
) -> Decimal:
    """
    Calculate monthly EMI (Equated Monthly Installment).
    
    Formula: EMI = [P x R x (1+R)^N]/[(1+R)^N-1]
    Where:
        P = Principal loan amount
        R = Monthly interest rate (annual rate / 12 / 100)
        N = Number of monthly installments
    
    Args:
        principal: Loan amount
        annual_rate: Annual interest rate percentage
        tenure_months: Loan tenure in months
    
    Returns:
        Monthly EMI amount
    """
    if tenure_months == 0:
        return Decimal('0')
    
    if annual_rate == 0:
        return principal / tenure_months
    
    # Convert annual rate to monthly rate
    monthly_rate = annual_rate / Decimal('12') / Decimal('100')
    
    # Calculate EMI using the formula
    numerator = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months)
    denominator = ((1 + monthly_rate) ** tenure_months) - 1
    
    emi = numerator / denominator
    return emi.quantize(Decimal('0.01'))


def calculate_approved_limit(monthly_salary: Decimal, multiplier: int = 36) -> Decimal:
    """
    Calculate approved credit limit based on monthly salary.
    
    Args:
        monthly_salary: Customer's monthly salary
        multiplier: Credit limit multiplier (default: 36)
    
    Returns:
        Approved credit limit
    """
    return (monthly_salary * multiplier).quantize(Decimal('0.01'))


def format_currency(amount: Decimal) -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
    
    Returns:
        Formatted currency string
    """
    return f"₹{amount:,.2f}"


def calculate_percentage(part: Decimal, whole: Decimal) -> float:
    """
    Calculate percentage safely.
    
    Args:
        part: Part value
        whole: Whole value
    
    Returns:
        Percentage value (0-100)
    """
    if whole == 0:
        return 0.0
    return float((part / whole) * 100)

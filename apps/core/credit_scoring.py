"""
Credit Scoring Algorithm for Loan Approval.

Implements the credit score calculation and loan approval logic
as per assignment requirements.
"""
from decimal import Decimal
from typing import Dict, Any, Tuple
from datetime import datetime

from apps.customers.models import Customer
from apps.loans.models import Loan
from .validators import validate_emi_to_salary_ratio


class CreditScorer:
    """
    Credit scoring engine for loan approval decisions.
    
    Scoring Components (per assignment):
    i. Past Loans paid on time: 20-40% based on performance
    ii. Number of loans taken in past: Higher = lower score
    iii. Loan activity in current year: More loans = lower score
    iv. Loan approved volume: Sum compared to approved limit
    v. Current loans > approved limit: Auto-reject
    """
    
    # Score weights
    PAYMENT_HISTORY_WEIGHT = 40  # Max points for perfect payment history
    LOAN_COUNT_WEIGHT = 20  # Points deducted for many loans
    CURRENT_YEAR_WEIGHT = 20  # Points deducted for recent loans
    VOLUME_WEIGHT = 20  # Points based on credit utilization
    
    def __init__(self, customer: Customer):
        """
        Initialize credit scorer for a customer.
        
        Args:
            customer: Customer instance to evaluate
        """
        self.customer = customer
        self.all_loans = list(customer.loans.all())
        self.active_loans = [loan for loan in self.all_loans if loan.is_active]
        self.current_year = datetime.now().year
    
    def calculate_credit_score(self) -> int:
        """
        Calculate overall credit score (0-100).
        
        Returns:
            Credit score between 0 and 100
        """
        if not self.all_loans:
            # New customer: default score of 50
            return 50
        
        payment_score = self._calculate_payment_history_score()
        loan_count_score = self._calculate_loan_count_score()
        current_year_score = self._calculate_current_year_score()
        volume_score = self._calculate_volume_score()
        
        total_score = (
            payment_score +
            loan_count_score +
            current_year_score +
            volume_score
        )
        
        # Ensure score is between 0 and 100
        return max(0, min(100, int(total_score)))
    
    def _calculate_payment_history_score(self) -> float:
        """
        Calculate score based on past loan payment history.
        
        Returns points between 0 and PAYMENT_HISTORY_WEIGHT based on
        percentage of EMIs paid on time across all loans.
        """
        total_emis = 0
        paid_on_time = 0
        
        for loan in self.all_loans:
            total_emis += loan.tenure
            paid_on_time += loan.emis_paid_on_time
        
        if total_emis == 0:
            return self.PAYMENT_HISTORY_WEIGHT / 2
        
        payment_percentage = paid_on_time / total_emis
        
        # Scale payment percentage to score weight
        score = payment_percentage * self.PAYMENT_HISTORY_WEIGHT
        
        return score
    
    def _calculate_loan_count_score(self) -> float:
        """
        Calculate score based on number of past loans.
        
        Returns points between 0 and LOAN_COUNT_WEIGHT.
        Fewer loans = higher score.
        """
        loan_count = len(self.all_loans)
        
        if loan_count == 0:
            return self.LOAN_COUNT_WEIGHT
        
        # Deduct points for each loan (max deduction at 10+ loans)
        deduction = min(loan_count * 2, self.LOAN_COUNT_WEIGHT)
        
        return self.LOAN_COUNT_WEIGHT - deduction
    
    def _calculate_current_year_score(self) -> float:
        """
        Calculate score based on loan activity in current year.
        
        Returns points between 0 and CURRENT_YEAR_WEIGHT.
        Fewer recent loans = higher score.
        """
        current_year_loans = [
            loan for loan in self.all_loans
            if loan.date_of_approval and loan.date_of_approval.year == self.current_year
        ]
        
        count = len(current_year_loans)
        
        if count == 0:
            return self.CURRENT_YEAR_WEIGHT
        
        # Deduct points for each current year loan (max deduction at 5+ loans)
        deduction = min(count * 4, self.CURRENT_YEAR_WEIGHT)
        
        return self.CURRENT_YEAR_WEIGHT - deduction
    
    def _calculate_volume_score(self) -> float:
        """
        Calculate score based on total loan volume vs approved limit.
        
        Returns points between 0 and VOLUME_WEIGHT based on credit utilization.
        Lower utilization = higher score.
        """
        if self.customer.approved_limit == 0:
            return 0
        
        # Credit utilization ratio
        utilization = float(self.customer.current_debt / self.customer.approved_limit)
        
        if utilization >= 1.0:
            # At or over limit = 0 points
            return 0
        
        # Higher utilization = fewer points
        score = (1 - utilization) * self.VOLUME_WEIGHT
        
        return score
    
    def evaluate_loan_eligibility(
        self,
        loan_amount: Decimal,
        tenure: int,
        interest_rate: Decimal
    ) -> Dict[str, Any]:
        """
        Evaluate loan eligibility and determine approval decision.
        
        Args:
            loan_amount: Requested loan amount
            tenure: Requested tenure in months
            interest_rate: Requested annual interest rate
        
        Returns:
            Dictionary with approval decision and details:
            {
                'approved': bool,
                'credit_score': int,
                'interest_rate': Decimal,
                'corrected_interest_rate': Decimal (if applicable),
                'monthly_installment': Decimal,
                'message': str
            }
        """
        from .utils import calculate_emi
        
        # Check if current loans exceed approved limit
        if self.customer.current_debt > self.customer.approved_limit:
            return {
                'approved': False,
                'credit_score': 0,
                'interest_rate': interest_rate,
                'corrected_interest_rate': interest_rate,
                'monthly_installment': Decimal('0'),
                'message': 'Current loans exceed approved limit'
            }
        
        # Calculate credit score
        credit_score = self.calculate_credit_score()
        
        # Determine approval and interest rate based on credit score
        approved = credit_score > 0  # Can approve with score > 0
        corrected_rate = self._determine_interest_rate(credit_score, interest_rate)
        
        # Calculate EMI
        emi = calculate_emi(loan_amount, corrected_rate, tenure)
        
        # Check EMI to salary ratio
        total_current_emi = sum(
            loan.monthly_repayment for loan in self.active_loans
        )
        new_total_emi = total_current_emi + emi
        
        emi_valid, emi_ratio = validate_emi_to_salary_ratio(
            new_total_emi,
            self.customer.monthly_salary
        )
        
        if not emi_valid:
            return {
                'approved': False,
                'credit_score': credit_score,
                'interest_rate': interest_rate,
                'corrected_interest_rate': corrected_rate,
                'monthly_installment': emi,
                'message': f'EMI to salary ratio ({emi_ratio:.2%}) exceeds 50% limit'
            }
        
        # Determine approval message
        if credit_score > 50:
            message = 'Loan approved'
        elif credit_score > 30:
            message = 'Loan approved with higher interest rate'
        elif credit_score > 10:
            message = 'Loan approved with significantly higher interest rate'
        else:
            approved = False
            message = 'Credit score too low for approval'
        
        return {
            'approved': approved,
            'credit_score': credit_score,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_rate,
            'monthly_installment': emi,
            'message': message
        }
    
    def _determine_interest_rate(
        self,
        credit_score: int,
        requested_rate: Decimal
    ) -> Decimal:
        """
        Determine interest rate based on credit score.
        
        Per assignment:
        - Score > 50: Approve at requested rate
        - 30 < Score <= 50: Approve at rate > 12%
        - 10 < Score <= 30: Approve at rate > 16%
        - Score <= 10: Don't approve
        
        Args:
            credit_score: Calculated credit score
            requested_rate: Customer's requested interest rate
        
        Returns:
            Corrected interest rate
        """
        if credit_score > 50:
            return requested_rate
        elif credit_score > 30:
            return max(requested_rate, Decimal('12.0'))
        elif credit_score > 10:
            return max(requested_rate, Decimal('16.0'))
        else:
            return requested_rate  # Will be rejected anyway

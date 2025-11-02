"""
API views for Loan endpoints.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.customers.models import Customer
from apps.core.credit_scoring import CreditScorer
from .models import Loan
from .serializers import (
    LoanEligibilityRequestSerializer,
    LoanEligibilityResponseSerializer,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    LoanDetailSerializer,
    CustomerLoansSerializer
)


class CheckEligibilityView(APIView):
    """
    API endpoint to check loan eligibility.
    POST /api/check-eligibility/
    """
    
    @extend_schema(
        request=LoanEligibilityRequestSerializer,
        responses={
            200: LoanEligibilityResponseSerializer,
            400: OpenApiResponse(description="Bad Request - Validation errors"),
            404: OpenApiResponse(description="Customer not found")
        },
        summary="Check loan eligibility",
        description="Check if customer is eligible for a loan and get corrected interest rate"
    )
    def post(self, request):
        """
        Check loan eligibility for a customer.
        
        Args:
            request: HTTP request with eligibility check data
        
        Returns:
            Eligibility decision with corrected interest rate
        """
        serializer = LoanEligibilityRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        try:
            customer = Customer.objects.get(customer_id=validated_data['customer_id'])
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Evaluate eligibility using credit scorer
        scorer = CreditScorer(customer)
        eligibility = scorer.evaluate_loan_eligibility(
            loan_amount=validated_data['loan_amount'],
            tenure=validated_data['tenure'],
            interest_rate=validated_data['interest_rate']
        )
        
        # Prepare response
        response_data = {
            'customer_id': customer.customer_id,
            'approved': eligibility['approved'],
            'interest_rate': validated_data['interest_rate'],
            'corrected_interest_rate': eligibility['corrected_interest_rate'],
            'tenure': validated_data['tenure'],
            'monthly_installment': eligibility['monthly_installment']
        }
        
        response_serializer = LoanEligibilityResponseSerializer(response_data)
        return Response(response_serializer.data)


class CreateLoanView(APIView):
    """
    API endpoint to create a new loan.
    POST /api/create-loan/
    """
    
    @extend_schema(
        request=CreateLoanRequestSerializer,
        responses={
            201: CreateLoanResponseSerializer,
            400: OpenApiResponse(description="Bad Request - Not eligible or validation errors"),
            404: OpenApiResponse(description="Customer not found")
        },
        summary="Create a new loan",
        description="Create a new loan after eligibility check"
    )
    def post(self, request):
        """
        Create a new loan for a customer.
        
        Automatically checks eligibility and rejects if not eligible.
        
        Args:
            request: HTTP request with loan data
        
        Returns:
            Loan creation confirmation
        """
        serializer = CreateLoanRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create loan (eligibility already checked in serializer)
        loan = serializer.save()
        
        response_data = {
            'loan_id': loan.loan_id,
            'customer_id': loan.customer.customer_id,
            'loan_approved': True,
            'message': 'Loan approved successfully',
            'monthly_installment': loan.monthly_repayment
        }
        
        response_serializer = CreateLoanResponseSerializer(response_data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class ViewLoanView(APIView):
    """
    API endpoint to view a specific loan.
    GET /api/view-loan/<loan_id>/
    """
    
    @extend_schema(
        responses={
            200: LoanDetailSerializer,
            404: OpenApiResponse(description="Loan not found")
        },
        summary="View loan details",
        description="Get detailed information about a specific loan"
    )
    def get(self, request, loan_id):
        """
        Get loan details by ID.
        
        Args:
            request: HTTP request
            loan_id: Loan ID
        
        Returns:
            Loan details
        """
        try:
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
            serializer = LoanDetailSerializer(loan)
            return Response(serializer.data)
        except Loan.DoesNotExist:
            return Response(
                {"error": "Loan not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ViewCustomerLoansView(APIView):
    """
    API endpoint to view all loans for a customer.
    GET /api/view-loans/<customer_id>/
    """
    
    @extend_schema(
        responses={
            200: CustomerLoansSerializer,
            404: OpenApiResponse(description="Customer not found")
        },
        summary="View customer's all loans",
        description="Get all loans for a specific customer"
    )
    def get(self, request, customer_id):
        """
        Get all loans for a customer.
        
        Args:
            request: HTTP request
            customer_id: Customer ID
        
        Returns:
            List of customer's loans
        """
        try:
            customer = Customer.objects.prefetch_related('loans').get(
                customer_id=customer_id
            )
            
            loans = customer.loans.all()
            
            response_data = {
                'customer_id': customer.customer_id,
                'loans': loans
            }
            
            serializer = CustomerLoansSerializer(response_data)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )


"""
API views for Customer endpoints.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Customer
from .serializers import (
    CustomerRegistrationSerializer,
    CustomerRegistrationResponseSerializer,
    CustomerDetailSerializer
)


class RegisterCustomerView(APIView):
    """
    API endpoint to register a new customer.
    POST /api/register/
    """
    
    @extend_schema(
        request=CustomerRegistrationSerializer,
        responses={
            201: CustomerRegistrationResponseSerializer,
            400: OpenApiResponse(description="Bad Request - Validation errors")
        },
        summary="Register a new customer",
        description="Register a new customer with automatic approved limit calculation"
    )
    def post(self, request):
        """
        Register a new customer.
        
        Args:
            request: HTTP request with customer data
        
        Returns:
            Customer details with approved_limit
        """
        serializer = CustomerRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            customer = serializer.save()
            response_serializer = CustomerRegistrationResponseSerializer(customer)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomerDetailView(APIView):
    """
    API endpoint to get customer details.
    GET /api/customers/<customer_id>/
    """
    
    @extend_schema(
        responses={
            200: CustomerDetailSerializer,
            404: OpenApiResponse(description="Customer not found")
        },
        summary="Get customer details",
        description="Retrieve detailed information about a customer"
    )
    def get(self, request, customer_id):
        """
        Get customer details by ID.
        
        Args:
            request: HTTP request
            customer_id: Customer ID
        
        Returns:
            Customer details
        """
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            serializer = CustomerDetailSerializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )


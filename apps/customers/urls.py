"""
URL configuration for customer app.
"""
from django.urls import path
from .views import RegisterCustomerView, CustomerDetailView

app_name = 'customers'

urlpatterns = [
    path('register/', RegisterCustomerView.as_view(), name='register'),
    path('customers/<int:customer_id>/', CustomerDetailView.as_view(), name='customer-detail'),
]

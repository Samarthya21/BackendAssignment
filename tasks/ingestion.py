"""
Celery tasks for data ingestion from CSV files.
"""
from celery import shared_task
from decimal import Decimal
from datetime import datetime
import pandas as pd
import logging

from apps.customers.models import Customer
from apps.loans.models import Loan

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def ingest_customer_data(self, csv_path: str) -> dict:
    """
    Ingest customer data from CSV file.
    
    Args:
        csv_path: Path to customerData.csv
    
    Returns:
        Dictionary with ingestion statistics
    """
    logger.info(f"Starting customer data ingestion from {csv_path}")
    
    stats = {
        'total_rows': 0,
        'created': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        stats['total_rows'] = len(df)
        
        logger.info(f"Read {stats['total_rows']} rows from CSV")
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Convert data types
                customer_data = {
                    'customer_id': int(row['Customer ID']),
                    'first_name': str(row['First Name']).strip(),
                    'last_name': str(row['Last Name']).strip(),
                    'age': int(row['Age']),
                    'phone_number': str(row['Phone Number']).strip(),
                    'monthly_salary': Decimal(str(row['Monthly Salary'])),
                    'approved_limit': Decimal(str(row['Approved Limit'])),
                    'current_debt': Decimal('0')  # Will be calculated from loans
                }
                
                # Create or update customer
                customer, created = Customer.objects.update_or_create(
                    customer_id=customer_data['customer_id'],
                    defaults=customer_data
                )
                
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
                
                # Update progress
                if (index + 1) % 100 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': index + 1,
                            'total': stats['total_rows'],
                            'status': f'Processing customer {index + 1} of {stats["total_rows"]}'
                        }
                    )
                
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Row {index + 1}: {str(e)}"
                stats['error_details'].append(error_msg)
                logger.error(error_msg)
        
        logger.info(
            f"Customer ingestion complete: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['errors']} errors"
        )
        
    except Exception as e:
        logger.error(f"Failed to ingest customer data: {str(e)}")
        stats['error_details'].append(f"File error: {str(e)}")
    
    return stats


@shared_task(bind=True)
def ingest_loan_data(self, csv_path: str) -> dict:
    """
    Ingest loan data from CSV file.
    
    Args:
        csv_path: Path to loanData.csv
    
    Returns:
        Dictionary with ingestion statistics
    """
    logger.info(f"Starting loan data ingestion from {csv_path}")
    
    stats = {
        'total_rows': 0,
        'created': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        stats['total_rows'] = len(df)
        
        logger.info(f"Read {stats['total_rows']} rows from CSV")
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Get customer
                customer_id = int(row['Customer ID'])
                try:
                    customer = Customer.objects.get(customer_id=customer_id)
                except Customer.DoesNotExist:
                    raise ValueError(f"Customer {customer_id} not found")
                
                # Parse dates
                date_of_approval = pd.to_datetime(row['Date of Approval']).date()
                end_date = pd.to_datetime(row['End Date']).date()
                
                # Convert data types
                loan_data = {
                    'customer': customer,
                    'loan_id': int(row['Loan ID']),
                    'loan_amount': Decimal(str(row['Loan Amount'])),
                    'tenure': int(row['Tenure']),
                    'interest_rate': Decimal(str(row['Interest Rate'])),
                    'monthly_repayment': Decimal(str(row['Monthly payment'])),
                    'emis_paid_on_time': int(row['EMIs paid on Time']),
                    'date_of_approval': date_of_approval,
                    'end_date': end_date
                }
                
                # Create or update loan
                loan, created = Loan.objects.update_or_create(
                    loan_id=loan_data['loan_id'],
                    defaults=loan_data
                )
                
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
                
                # Update progress
                if (index + 1) % 100 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': index + 1,
                            'total': stats['total_rows'],
                            'status': f'Processing loan {index + 1} of {stats["total_rows"]}'
                        }
                    )
                
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Row {index + 1}: {str(e)}"
                stats['error_details'].append(error_msg)
                logger.error(error_msg)
        
        logger.info(
            f"Loan ingestion complete: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['errors']} errors"
        )
        
    except Exception as e:
        logger.error(f"Failed to ingest loan data: {str(e)}")
        stats['error_details'].append(f"File error: {str(e)}")
    
    return stats


@shared_task
def update_all_customer_debts():
    """
    Update current_debt for all customers based on their active loans.
    Should be run after loan data ingestion.
    """
    logger.info("Starting customer debt update")
    
    updated_count = 0
    error_count = 0
    
    for customer in Customer.objects.all():
        try:
            customer.update_current_debt()
            updated_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to update debt for customer {customer.customer_id}: {str(e)}")
    
    logger.info(f"Debt update complete: {updated_count} updated, {error_count} errors")
    
    return {
        'updated': updated_count,
        'errors': error_count
    }


@shared_task(bind=True)
def ingest_all_data(self, customer_csv_path: str, loan_csv_path: str) -> dict:
    """
    Ingest both customer and loan data, then update customer debts.
    
    Args:
        customer_csv_path: Path to customerData.csv
        loan_csv_path: Path to loanData.csv
    
    Returns:
        Dictionary with combined ingestion statistics
    """
    logger.info("Starting full data ingestion")
    
    # Update task state
    self.update_state(
        state='PROGRESS',
        meta={'status': 'Ingesting customer data...'}
    )
    
    # Ingest customers
    customer_stats = ingest_customer_data(customer_csv_path)
    
    # Update task state
    self.update_state(
        state='PROGRESS',
        meta={'status': 'Ingesting loan data...'}
    )
    
    # Ingest loans
    loan_stats = ingest_loan_data(loan_csv_path)
    
    # Update task state
    self.update_state(
        state='PROGRESS',
        meta={'status': 'Updating customer debts...'}
    )
    
    # Update customer debts
    debt_stats = update_all_customer_debts()
    
    logger.info("Full data ingestion complete")
    
    return {
        'customers': customer_stats,
        'loans': loan_stats,
        'debt_updates': debt_stats
    }

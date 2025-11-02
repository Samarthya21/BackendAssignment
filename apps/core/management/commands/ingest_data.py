"""
Django management command to ingest CSV data.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os

from tasks.ingestion import ingest_all_data


class Command(BaseCommand):
    help = 'Ingest customer and loan data from CSV files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-file',
            type=str,
            default='data/customerData.csv',
            help='Path to customer CSV file (relative to project root)'
        )
        parser.add_argument(
            '--loan-file',
            type=str,
            default='data/loanData.csv',
            help='Path to loan CSV file (relative to project root)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run ingestion as async Celery task'
        )
    
    def handle(self, *args, **options):
        customer_file = options['customer_file']
        loan_file = options['loan_file']
        run_async = options['async']
        
        # Convert to absolute paths
        if not os.path.isabs(customer_file):
            customer_file = os.path.join(settings.BASE_DIR, customer_file)
        if not os.path.isabs(loan_file):
            loan_file = os.path.join(settings.BASE_DIR, loan_file)
        
        # Check if files exist
        if not os.path.exists(customer_file):
            self.stdout.write(
                self.style.ERROR(f'Customer file not found: {customer_file}')
            )
            return
        
        if not os.path.exists(loan_file):
            self.stdout.write(
                self.style.ERROR(f'Loan file not found: {loan_file}')
            )
            return
        
        self.stdout.write(f'Customer file: {customer_file}')
        self.stdout.write(f'Loan file: {loan_file}')
        
        if run_async:
            # Run as Celery task
            self.stdout.write(
                self.style.WARNING('Starting async ingestion task...')
            )
            task = ingest_all_data.delay(customer_file, loan_file)
            self.stdout.write(
                self.style.SUCCESS(f'Task started with ID: {task.id}')
            )
            self.stdout.write(
                'Check task status with: celery -A config inspect active'
            )
        else:
            # Run synchronously
            self.stdout.write(
                self.style.WARNING('Starting synchronous ingestion...')
            )
            result = ingest_all_data(customer_file, loan_file)
            
            # Display results
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('INGESTION COMPLETE'))
            self.stdout.write('='*50)
            
            # Customer stats
            customer_stats = result['customers']
            self.stdout.write('\nCustomers:')
            self.stdout.write(f"  Total rows: {customer_stats['total_rows']}")
            self.stdout.write(
                self.style.SUCCESS(f"  Created: {customer_stats['created']}")
            )
            self.stdout.write(
                self.style.WARNING(f"  Updated: {customer_stats['updated']}")
            )
            if customer_stats['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(f"  Errors: {customer_stats['errors']}")
                )
                for error in customer_stats['error_details'][:5]:
                    self.stdout.write(f"    - {error}")
            
            # Loan stats
            loan_stats = result['loans']
            self.stdout.write('\nLoans:')
            self.stdout.write(f"  Total rows: {loan_stats['total_rows']}")
            self.stdout.write(
                self.style.SUCCESS(f"  Created: {loan_stats['created']}")
            )
            self.stdout.write(
                self.style.WARNING(f"  Updated: {loan_stats['updated']}")
            )
            if loan_stats['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(f"  Errors: {loan_stats['errors']}")
                )
                for error in loan_stats['error_details'][:5]:
                    self.stdout.write(f"    - {error}")
            
            # Debt update stats
            debt_stats = result['debt_updates']
            self.stdout.write('\nDebt Updates:')
            self.stdout.write(
                self.style.SUCCESS(f"  Updated: {debt_stats['updated']}")
            )
            if debt_stats['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(f"  Errors: {debt_stats['errors']}")
                )
            
            self.stdout.write('\n' + '='*50)

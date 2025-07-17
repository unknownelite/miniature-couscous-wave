# your_app/management/commands/process_daily_interest.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from core.models import Investment, Transaction, User

class Command(BaseCommand):
    help = 'Process daily interest for all active investments'

    def handle(self, *args, **options):
        now = timezone.now()
        processed_count = 0
        
        # Get all active investments with select_related for optimization
        active_investments = Investment.objects.filter(
            is_active=True
        ).select_related('user', 'plan')
        
        with transaction.atomic():
            for investment in active_investments:
                # Calculate days since last interest payment
                days_passed = (now - investment.last_interest_date).days
                
                if days_passed >= 1:
                    # Calculate interest for all pending days
                    interest = (investment.amount * investment.plan.daily_percentage / Decimal('100') * days_passed).quantize(Decimal('0.01'))
                    
                    # Update user balance
                    user = investment.user
                    user.available_balance += interest
                    user.save()
                    
                    # Create transaction
                    Transaction.objects.create(
                        user=user,
                        transaction_type='interest',
                        amount=interest,
                        status='successful',
                        description=f"{days_passed} day(s) interest from {investment.plan.name}"
                    )
                    
                    # Update investment
                    investment.last_interest_date = now
                    if now - investment.date_invested >= timedelta(days=28):
                        investment.can_withdraw = True
                        investment.next_withdrawal_date = now + timedelta(days=28)
                    investment.save()
                    
                    processed_count += 1
                    self.stdout.write(f"Processed interest for investment ID {investment.id} - ${interest}")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully processed interest for {processed_count} investments"))
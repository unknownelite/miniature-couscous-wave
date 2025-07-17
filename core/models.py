from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import uuid
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db.models import JSONField
from django.core.cache import cache
# from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    middle_name = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True)
    available_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_invested = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    mining_points = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=10, default='en')
    is_verified = models.BooleanField(default=False)
    # phone_number = PhoneNumberField(blank=True)  # Uses phonenumbers lib
       
    # Wallet addresses
    cashapp_tag = models.CharField(max_length=50, blank=True)
    paypal_email = models.EmailField(blank=True)
    bank_account = models.TextField(blank=True)
    usdt_address = models.CharField(max_length=100, blank=True)
    btc_address = models.CharField(max_length=100, blank=True)
    eth_address = models.CharField(max_length=100, blank=True)

class InvestmentPlan(models.Model):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=50)
    min_amount = models.DecimalField(max_digits=20, decimal_places=2)
    daily_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    mining_points_rate = models.PositiveIntegerField()  # Points per dollar
    
    def __str__(self):
        return self.name

class Investment(models.Model):
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(
        max_digits=20, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date_invested = models.DateTimeField(auto_now_add=True)
    last_interest_date = models.DateTimeField(auto_now_add=True)
    daily_interest = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    can_withdraw = models.BooleanField(default=False)
    next_withdrawal_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_invested']
        verbose_name = "User Investment"
        verbose_name_plural = "User Investments"

    def __str__(self):
        return f"{self.user.username}'s {self.plan.name if self.plan else 'No Plan'} Investment (${self.amount})"

    def clean(self):
        """Validate the investment before saving"""
        super().clean()
        
        if not self.plan:
            raise ValidationError("Investment plan is required")
            
        if self.amount < self.plan.min_amount:
            raise ValidationError(
                f"Amount must be at least ${self.plan.min_amount} for this plan"
            )
            
        expected_interest = self.calculate_proper_daily_interest()
        if abs(self.daily_interest - expected_interest) > Decimal('0.01'):
            raise ValidationError({
                'daily_interest': (
                    f"Incorrect daily interest. Should be ${expected_interest:.2f} "
                    f"({self.plan.daily_percentage}% of ${self.amount})"
                )
            })

    def save(self, *args, **kwargs):
        """Override save to ensure proper calculations and withdrawal dates"""
        now = timezone.now()
        
        # Calculate daily interest
        if self.plan and self.amount:
            self.daily_interest = self.calculate_proper_daily_interest()
        
        # Set initial dates for new investments
        if not self.pk:  # New investment
            self.date_invested = now
            self.last_interest_date = now
            self.next_withdrawal_date = now + timedelta(days=28)
            self.can_withdraw = False
        else:
            # Update withdrawal status for existing investments
            if now >= self.next_withdrawal_date:
                self.can_withdraw = True
                # Set next withdrawal window (28 days from now)
                self.next_withdrawal_date = now + timedelta(days=28)
            else:
                self.can_withdraw = False
        
        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_proper_daily_interest(self):
        """Calculate the correct daily interest based on plan percentage"""
        if self.plan and self.amount:
            return (self.amount * self.plan.daily_percentage / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def get_expected_interest_per_period(self, days=30):
        """Calculate expected interest for a given period"""
        return (self.daily_interest * Decimal(days)).quantize(Decimal('0.01'))

    @property
    def days_active(self):
        """Calculate how many days the investment has been active"""
        return (timezone.now() - self.date_invested).days

    @property
    def days_until_withdrawal(self):
        """Calculate remaining days until withdrawal is allowed"""
        if self.can_withdraw:
            return 0
        return (self.next_withdrawal_date - timezone.now()).days

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('interest', 'Interest'),
        ('mining', 'Mining Points Conversion'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    )
    
    CURRENCY_CHOICES = (
        ('USDT', 'USDT (TRC20)'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    proof = models.FileField(upload_to='payment_proofs/', null=True, blank=True)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"

class KYCDocument(models.Model):
    DOCUMENT_TYPES = (
    ('passport', 'Passport'),
    ('driver_license', "Driver's License"),
    ('national_id', 'National ID Card'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100)
    front_image = models.ImageField(upload_to='kyc_docs/')
    back_image = models.ImageField(upload_to='kyc_docs/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.document_type}"

class SystemWallet(models.Model):
    CURRENCY_CHOICES = [
        ('USDT', 'USDT (TRC20)'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
    ]
    
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, unique=True)
    address = models.CharField(max_length=100)
    qr_code = models.ImageField(upload_to='wallet_qr_codes/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_currency_display()} Wallet"
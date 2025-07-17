from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import *
from .forms import *
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import time
# from two_factor.views import SetupView
# from two_factor.plugins.phonenumber.models import PhoneDevice  # Updated import
# from django_otp.plugins.otp_email.models import EmailDevice



def index(request):
    plans = InvestmentPlan.objects.all()
    return render(request, 'index.html', {'plans': plans})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next') or 'dashboard'
                return redirect(next_url)
        messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm(request)
        
    return render(request, 'login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })
    

def terms_view(request):
    context = {
        "last_updated": "January 1, 2024"  # Dynamic date
    }
    return render(request, "terms.html", context)

def privacy_view(request):
    context = {
        "last_updated": "January 1, 2024"
    }
    return render(request, "privacy.html", context)

def faq_view(request):
    return render(request, 'faq.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

@login_required

def dashboard(request):

    try:

        # Optimize queries with select_related and only needed fields

        investments = Investment.objects.filter(

            user=request.user,

            is_active=True

        ).select_related('plan').only(

            'amount', 'date_invested', 'last_interest_date',

            'can_withdraw', 'next_withdrawal_date', 'plan__name',

            'plan__daily_percentage'

        )

        

        recent_transactions = Transaction.objects.filter(

            user=request.user

        ).order_by('-date')[:5].only(

            'transaction_type', 'amount', 'status',

            'description', 'date'

        )



        # Calculate actual growth percentage based on investments

        total_invested = request.user.total_invested

        total_earned = sum(

            inv.amount * (inv.plan.daily_percentage / 100) * 

            (timezone.now() - inv.date_invested).days

            for inv in investments

        )

        growth_percentage = (total_earned / total_invested * 100) if total_invested > 0 else 0



        # Tier system calculation

        tiers = [500, 1000, 5000, 10000, float('inf')]

        user_total = float(request.user.total_invested)

        current_tier = next((i for i, val in enumerate(tiers) if user_total < val), len(tiers)-1)

        next_tier_amount = tiers[current_tier] - user_total if current_tier < len(tiers)-1 else 0

        tier_progress = min(100, (user_total / tiers[current_tier]) * 100) if current_tier < len(tiers)-1 else 100



        # Process daily interest and mining conversion in atomic transaction

        now = timezone.now()

        with transaction.atomic():

            # Process daily interests

            for investment in investments:

                if now - investment.last_interest_date >= timedelta(days=1):

                    interest = (investment.amount * (investment.plan.daily_percentage / 100)).quantize(Decimal('0.01'))

                    request.user.available_balance += interest

                    

                    Transaction.objects.create(

                        user=request.user,

                        transaction_type='interest',

                        amount=interest,

                        status='successful',

                        description=f"Daily interest from {investment.plan.name}"

                    )

                    

                    investment.last_interest_date = now

                    if now - investment.date_invested >= timedelta(days=28):

                        investment.can_withdraw = True

                        investment.next_withdrawal_date = now + timedelta(days=28)

                    investment.save()



            # Process monthly mining conversion

            if now.day >= 28 and request.user.mining_points > 0:

                conversion_rate = Decimal('0.0005')

                amount = (request.user.mining_points * conversion_rate).quantize(Decimal('0.01'))

                request.user.available_balance += amount

                request.user.mining_points = 0

                

                Transaction.objects.create(

                    user=request.user,

                    transaction_type='mining',

                    amount=amount,

                    status='successful',

                    description="Monthly mining points conversion"

                )

            

            request.user.save()



        context = {

            'active_investments': investments,

            'recent_transactions': recent_transactions,

            'growth_percentage': round(growth_percentage, 2),

            'next_conversion_date': now.replace(day=28) + timedelta(days=1),

            'mining_value': (request.user.mining_points * Decimal('0.0005')).quantize(Decimal('0.01')),

            'next_tier_amount': Decimal(next_tier_amount).quantize(Decimal('0.01')),

            'tier_progress': round(tier_progress, 2),

            'current_tier': current_tier + 1,  # 1-based index for display

            'total_balance': request.user.available_balance.quantize(Decimal('0.01')),

        }



        return render(request, 'dashboard/home.html', context)



    except Exception as e:

        # Log the full error for debugging

        print(f"Dashboard Error: {str(e)}")

        # Return basic context even if processing fails

        return render(request, 'dashboard/home.html', {

            'active_investments': [],

            'recent_transactions': [],

            'error_message': 'Could not load dashboard data'

        })


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # Set a timestamp in session when profile pic changes
            if 'profile_pic' in request.FILES:
                request.session['profile_pic_timestamp'] = str(int(time.time()))
                messages.success(request, 'Profile picture updated successfully!')
            else:
                messages.success(request, 'Profile updated successfully')
                
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'dashboard/profile.html', {'form': form})

@login_required
def invest_view(request):
    try:
        # Get active investment plans - remove is_active filter if field doesn't exist
        plans = InvestmentPlan.objects.all()  # Or use your actual active/inactive field if available
        
        # Get user's active investments
        investments = Investment.objects.filter(
            user=request.user, 
            is_active=True
        ).select_related('plan').only(
            'amount', 'date_invested', 'last_interest_date',
            'daily_interest', 'can_withdraw', 'next_withdrawal_date',
            'plan__name', 'plan__daily_percentage'
        )
        
        if request.method == 'POST':
            form = InvestmentForm(request.POST, user=request.user)
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        plan = form.cleaned_data['plan_id']
                        min_amount = plan.min_amount
                        
                        daily_interest = (min_amount * plan.daily_percentage / Decimal('100')).quantize(Decimal('0.01'))
                        
                        investment = Investment.objects.create(
                            user=request.user,
                            plan=plan,
                            amount=min_amount,
                            daily_interest=daily_interest,
                            date_invested=timezone.now(),
                            last_interest_date=timezone.now(),
                            next_withdrawal_date=timezone.now() + timedelta(days=28),
                            is_active=True  # Ensure this field exists in your Investment model
                        )
                        
                        request.user.available_balance -= min_amount
                        request.user.total_invested += min_amount
                        request.user.mining_points += int(min_amount * plan.mining_points_rate)
                        request.user.save()
                        
                        messages.success(request, f'Successfully invested ${min_amount} in {plan.name}')
                        return redirect('invest')
                
                except Exception as e:
                    messages.error(request, 'Error processing investment')
                    print(f"Investment error: {str(e)}")
                    return redirect('invest')
        
        else:
            form = InvestmentForm(user=request.user)

        context = {
            'plans': plans,
            'investments': investments,
            'form': form
        }
        return render(request, 'dashboard/invest.html', context)
    
    except Exception as e:
        print(f"View error: {str(e)}")
        messages.error(request, 'System error')
        return redirect('invest')

@login_required
def withdraw_view(request):
    MIN_WITHDRAWAL = Decimal('50.00')
    WITHDRAWAL_FEE = Decimal('1.00')
    
    # Calculate next withdrawal date based on active investments
    active_investments = Investment.objects.filter(
        user=request.user,
        is_active=True
    )
    
    # Get the earliest next withdrawal date from active investments
    next_withdrawal_date = None
    for investment in active_investments:
        if investment.next_withdrawal_date:
            if next_withdrawal_date is None or investment.next_withdrawal_date < next_withdrawal_date:
                next_withdrawal_date = investment.next_withdrawal_date
    
    # Check if user has any non-withdrawable investments
    locked_investments = active_investments.filter(can_withdraw=False).exists()
    
    # Helper function to get withdrawal destination display
    def get_withdrawal_destination(user, method):
        """Get formatted withdrawal destination for display"""
        if method == 'cashapp':
            return f"${user.cashapp_tag}" if user.cashapp_tag else "CashApp"
        elif method == 'paypal':
            return user.paypal_email if user.paypal_email else "PayPal"
        elif method == 'bank':
            return user.bank_account if user.bank_account else "Bank Account"
        elif method == 'usdt':
            return f"USDT: {user.usdt_address[:10]}..." if user.usdt_address else "USDT"
        elif method == 'btc':
            return f"BTC: {user.btc_address[:10]}..." if user.btc_address else "Bitcoin"
        elif method == 'eth':
            return f"ETH: {user.eth_address[:10]}..." if user.eth_address else "Ethereum"
        return method

    def send_withdrawal_notification(user, amount, method):
        """Send withdrawal notification to user"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        subject = f"Withdrawal Request Confirmation - ${amount}"
        html_message = render_to_string('withdrawal_request.html', {
            'user': user,
            'amount': amount,
            'method': method,
            'fee': WITHDRAWAL_FEE,
            'net_amount': amount - WITHDRAWAL_FEE,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            'mrsingle444425@gmail.com',  # From email
            [user.email],  # To email
            html_message=html_message,
            fail_silently=False,
        )

    # Get available withdrawal methods
    available_methods = []
    if request.user.cashapp_tag:
        available_methods.append(('cashapp', f"CashApp - {request.user.cashapp_tag}"))
    if request.user.paypal_email:
        available_methods.append(('paypal', f"PayPal - {request.user.paypal_email}"))
    if request.user.bank_account:
        available_methods.append(('bank', "Bank Transfer"))
    if request.user.usdt_address:
        available_methods.append(('usdt', f"USDT - {request.user.usdt_address[:10]}..."))
    if request.user.btc_address:
        available_methods.append(('btc', f"Bitcoin - {request.user.btc_address[:10]}..."))
    if request.user.eth_address:
        available_methods.append(('eth', f"Ethereum - {request.user.eth_address[:10]}..."))

    withdrawals = Transaction.objects.filter(
        user=request.user,
        transaction_type='withdrawal'
    ).order_by('-date')[:10]

    # Check if user has any non-withdrawable investments
    locked_investments = Investment.objects.filter(
        user=request.user,
        is_active=True,
        can_withdraw=False
    ).exists()

    if request.method == 'POST':
        form = WithdrawalForm(request.user, request.POST, available_methods=available_methods)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            method = form.cleaned_data['method']
            total_amount = amount + WITHDRAWAL_FEE

            try:
                with transaction.atomic():
                    # Check for locked investments
                    if locked_investments:
                        messages.error(
                            request,
                            "⚠️ You cannot withdraw while you have active investments "
                            "that haven't reached their 28-day maturity period."
                        )
                        return redirect('withdraw')

                    # Validate minimum amount
                    if amount < MIN_WITHDRAWAL:
                        messages.error(
                            request,
                            f"Minimum withdrawal amount is ${MIN_WITHDRAWAL}. "
                            f"You tried to withdraw ${amount:.2f}"
                        )
                        return redirect('withdraw')

                    # Validate available balance
                    if request.user.available_balance < total_amount:
                        messages.error(
                            request,
                            f"Insufficient balance. You requested ${amount:.2f} + "
                            f"${WITHDRAWAL_FEE} fee = ${total_amount:.2f} "
                            f"(Available: ${request.user.available_balance:.2f})"
                        )
                        return redirect('withdraw')

                    # Process withdrawal
                    request.user.available_balance -= total_amount
                    request.user.total_withdrawn += amount
                    request.user.save()

                    # Create transactions
                    withdrawal = Transaction.objects.create(
                        user=request.user,
                        transaction_type='withdrawal',
                        amount=-amount,
                        status='pending',
                        description=(
                            f"Method: {method}|"
                            f"Destination: {get_withdrawal_destination(request.user, method)}|"
                            f"Fee: {WITHDRAWAL_FEE}|"
                            f"Net Amount: {amount - WITHDRAWAL_FEE}"
                        )
                    )

                    Transaction.objects.create(
                        user=request.user,
                        transaction_type='fee',
                        amount=-WITHDRAWAL_FEE,
                        status='completed',
                        description=f"Withdrawal fee for {method} transfer"
                    )

                    # Send email notification
                    send_withdrawal_notification(request.user, amount, method)

                    messages.success(
                        request,
                        f"✅ Withdrawal of ${amount:.2f} submitted for approval. "
                        f"${WITHDRAWAL_FEE} fee deducted. "
                        "You'll receive a confirmation email shortly."
                    )
                    return redirect('withdraw')

            except Exception as e:
                messages.error(
                    request,
                    "❌ System error processing withdrawal. Please try again later."
                )
                print(f"Withdrawal processing error: {str(e)}")
                return redirect('withdraw')
    else:
        form = WithdrawalForm(request.user, available_methods=available_methods)

    context = {
        'form': form,
        'available_balance': request.user.available_balance,
        'min_withdrawal': MIN_WITHDRAWAL,
        'withdrawal_fee': WITHDRAWAL_FEE,
        'withdrawals': withdrawals,
        'locked_investments': locked_investments,  # Pass to template
        'next_withdrawal_date': next_withdrawal_date,
    }
    return render(request, 'dashboard/withdraw.html', context)

@login_required
def transactions_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'dashboard/transactions.html', {'transactions': transactions})

@login_required
def fund_view(request):
    def get_wallet(currency):
        cache_key = f'wallet_{currency.lower()}'
        wallet = cache.get(cache_key)
        if not wallet:
            wallet = SystemWallet.objects.filter(
                currency=currency.upper(), 
                is_active=True
            ).first()
            if wallet:
                cache.set(cache_key, wallet, 60*60*24)  # Cache for 24 hours
        return wallet

    # Get active wallets for each currency
    usdt_wallet = get_wallet('USDT')
    btc_wallet = get_wallet('BTC')
    eth_wallet = get_wallet('ETH')
    
    # Get user's deposit history
    deposits = Transaction.objects.filter(
        user=request.user,
        transaction_type='deposit'
    ).order_by('-date')[:10]
    
    # Calculate total deposited
    total_deposited = Transaction.objects.filter(
        user=request.user,
        transaction_type='deposit',
        status='successful'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    if request.method == 'POST':
        form = FundForm(request.POST, request.FILES)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            currency = form.cleaned_data['currency']
            proof = form.cleaned_data.get('proof')
            
            # Create deposit transaction
            Transaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                status='pending',
                description=f"Deposit request via {currency}",
                proof=proof,
                currency=currency.upper()
            )
            
            messages.success(
                request,
                f'Deposit of ${amount:.2f} via {currency} submitted. '
                'Your funds will be credited after verification.'
            )
            return redirect('dashboard')
    else:
        form = FundForm()

    context = {
        'form': form,
        'usdt_wallet': usdt_wallet,
        'btc_wallet': btc_wallet,
        'eth_wallet': eth_wallet,
        'deposits': deposits,
        'total_deposited': total_deposited
    }
    return render(request, 'dashboard/fund.html', context)

@login_required
def kyc_view(request):
    try:
        kyc = KYCDocument.objects.get(user=request.user)
    except KYCDocument.DoesNotExist:
        kyc = None
    
    if request.method == 'POST':
        form = KYCForm(request.POST, request.FILES)
        if form.is_valid():
            if kyc:
                kyc.document_type = form.cleaned_data['document_type']
                kyc.document_number = form.cleaned_data['document_number']
                kyc.front_image = form.cleaned_data['front_image']
                if form.cleaned_data['back_image']:
                    kyc.back_image = form.cleaned_data['back_image']
                kyc.status = 'pending'
                kyc.save()
            else:
                KYCDocument.objects.create(
                    user=request.user,
                    document_type=form.cleaned_data['document_type'],
                    document_number=form.cleaned_data['document_number'],
                    front_image=form.cleaned_data['front_image'],
                    back_image=form.cleaned_data['back_image'],
                    status='pending'
                )
            
            messages.success(request, 'KYC documents submitted for verification')
            return redirect('kyc')
    else:
        initial = {}
        if kyc:
            initial = {
                'document_type': kyc.document_type,
                'document_number': kyc.document_number
            }
        form = KYCForm(initial=initial)
    
    return render(request, 'dashboard/kyc.html', {'form': form, 'kyc': kyc})

@login_required
def settings_view(request):
    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Password changed successfully')
                return redirect('settings')
        elif 'change_language' in request.POST:
            language_form = LanguageForm(request.POST, instance=request.user)
            if language_form.is_valid():
                language_form.save()
                messages.success(request, 'Language preference updated')
                return redirect('settings')
    else:
        password_form = PasswordChangeForm(request.user)
        language_form = LanguageForm(instance=request.user)
    
    return render(request, 'dashboard/settings.html', {
        'password_form': password_form,
        'language_form': language_form
    })
    
@require_POST
def delete_account(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    password = request.POST.get('password')
    user = authenticate(username=request.user.username, password=password)
    
    if user is not None:
        # Delete the user account
        user.delete()
        logout(request)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Incorrect password'})
    




# class CustomSetupView(SetupView):
#     def get_method_choices(self):
#         choices = super().get_method_choices()
#         choices.append(('sms', 'SMS (Twilio)'))  # Requires Twilio config
#         return choices

# def disable_2fa(request):
#     if request.method == 'POST':
#         # Disable logic here
#         return JsonResponse({'success': True})
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# def backup_codes(request):
#     if not request.user.is_authenticated:
#         return redirect('login')
#     return render(request, 'dashboard/backup_codes.html')
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import *
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'required': 'required'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        }),
        help_text="<small>Minimum 8 characters, not too common, not entirely numeric</small>"
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
                'autofocus': 'autofocus'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = ''
        self.fields['password'].label = ''

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'middle_name', 'last_name', 'dob', 'profile_pic',
                  'cashapp_tag', 'paypal_email', 'bank_account', 
                  'usdt_address', 'btc_address', 'eth_address']

class WithdrawalForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        available_methods = kwargs.pop('available_methods', None)
        super().__init__(*args, **kwargs)
        self.user = user
        
        method_choices = []
        if available_methods:  # Use passed methods if available
            method_choices = available_methods
        else:  # Fall back to checking user's payment methods
            if user.cashapp_tag:
                method_choices.append(('cashapp', 'CashApp'))
            if user.paypal_email:
                method_choices.append(('paypal', 'PayPal'))
            if user.bank_account:
                method_choices.append(('bank', 'Bank Transfer'))
            if user.usdt_address:
                method_choices.append(('usdt', 'USDT'))
            if user.btc_address:
                method_choices.append(('btc', 'Bitcoin'))
            if user.eth_address:
                method_choices.append(('eth', 'Ethereum'))
        
        self.fields['method'] = forms.ChoiceField(choices=method_choices)
    
    amount = forms.DecimalField(min_value=10, max_digits=20, decimal_places=2)
    method = forms.ChoiceField(choices=[])

class FundForm(forms.Form):
    amount = forms.DecimalField(
        min_value=500,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum $500'
        })
    )
    currency = forms.ChoiceField(
        choices=[
            ('usdt', 'USDT (TRC20)'),
            ('btc', 'Bitcoin (BTC)'),
            ('eth', 'Ethereum (ETH)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    proof = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'file-input'})
    )

class KYCForm(forms.Form):
    DOCUMENT_TYPES = [
        ('passport', 'Passport'),
        ('driver_license', 'Driver License'),
        ('national_id', 'National ID'),
    ]
    
    document_type = forms.ChoiceField(choices=DOCUMENT_TYPES)
    document_number = forms.CharField(max_length=100)
    front_image = forms.ImageField()
    back_image = forms.ImageField(required=False)

class LanguageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['language']
        widgets = {
            'language': forms.Select(choices=[
                ('en', 'English'),
                ('es', 'Spanish'),
                ('fr', 'French'),
                ('de', 'German'),
                ('zh', 'Chinese'),
            ])
        }
        
class InvestmentForm(forms.Form):
    plan_id = forms.ModelChoiceField(
        queryset=InvestmentPlan.objects.all(),
        widget=forms.HiddenInput(),
        error_messages={
            'required': 'Please select an investment plan',
            'invalid_choice': 'The selected plan is not available'
        }
    )
    
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['plan_id'].queryset = InvestmentPlan.objects.filter(is_active=True)
        self.fields['plan_id'].widget.attrs.update({
            'id': 'formPlanId',
            'class': 'hidden-plan-input'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        plan = cleaned_data.get('plan_id')
        
        if not plan:
            return cleaned_data  # Let ModelChoiceField handle the required validation
            
        # Check user balance
        if self.user.available_balance < plan.min_amount:
            raise forms.ValidationError(
                f"Insufficient balance. You need ${plan.min_amount}, but only have ${self.user.available_balance:.2f}"
            )
            
        # Check for existing active investment in this plan
        if Investment.objects.filter(
            user=self.user, 
            plan=plan, 
            is_active=True
        ).exists():
            raise forms.ValidationError(
                f"You already have an active investment in the {plan.name} plan"
            )
        
        # Validate plan properties
        if not hasattr(plan, 'daily_percentage') or plan.daily_percentage <= 0:
            raise forms.ValidationError(
                "Selected plan has invalid daily percentage"
            )
            
        if plan.min_amount <= 0:
            raise forms.ValidationError(
                "Selected plan has invalid minimum amount"
            )
            
        return cleaned_data
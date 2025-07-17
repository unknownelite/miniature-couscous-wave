from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, InvestmentPlan, Investment, Transaction, KYCDocument, SystemWallet

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'total_invested', 'available_balance')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'middle_name', 'last_name', 'email', 'dob', 'profile_pic')}),
        ('Financial Info', {'fields': ('available_balance', 'total_invested', 'total_withdrawn', 'mining_points')}),
        ('Payment Methods', {'fields': ('cashapp_tag', 'paypal_email', 'bank_account', 'usdt_address', 'btc_address', 'eth_address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_amount', 'daily_percentage', 'mining_points_rate')
    search_fields = ('name',)

class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'date_invested', 'is_active', 'can_withdraw')
    list_filter = ('is_active', 'can_withdraw', 'plan')
    search_fields = ('user__username', 'plan__name')

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'status', 'date')
    list_filter = ('transaction_type', 'status')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'date'

class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'submitted_at', 'processed_at')
    list_filter = ('status', 'document_type')
    search_fields = ('user__username', 'document_number')
    readonly_fields = ('submitted_at',)

class SystemWalletAdmin(admin.ModelAdmin):
    list_display = ('currency', 'address', 'is_active')
    list_filter = ('is_active', 'currency')

admin.site.register(User, CustomUserAdmin)
admin.site.register(InvestmentPlan, InvestmentPlanAdmin)
admin.site.register(Investment, InvestmentAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(KYCDocument, KYCDocumentAdmin)
admin.site.register(SystemWallet, SystemWalletAdmin)
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.profile_view, name='profile'),
    path('dashboard/invest/', views.invest_view, name='invest'),
    path('dashboard/withdraw/', views.withdraw_view, name='withdraw'),
    path('dashboard/transactions/', views.transactions_view, name='transactions'),
    path('dashboard/fund/', views.fund_view, name='fund'),
    path('dashboard/kyc/', views.kyc_view, name='kyc'),
    path('dashboard/settings/', views.settings_view, name='settings'),
    path('delete-account/', views.delete_account, name='delete_account'),
    
    # Homepage
    path('', views.index, name='index'),
    path("terms/", views.terms_view, name="terms"),
    path("privacy/", views.privacy_view, name="privacy"),
    path('faq/', views.faq_view, name='faq'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Password Change
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='dashboard/password_change.html',
             success_url='/password-change-done/'
         ), 
         name='password_change'),
    path('password-change-done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='dashboard/password_change_done.html'
         ), 
         name='password_change_done'),
    
]
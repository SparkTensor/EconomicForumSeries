from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.efs_login, name='efs_login'),
    path('signup/email_verification/', views.efs_verification_email_sent, name='efs_verification_email_sent'),
    # The baban'la of views
    path('signup/<event_id>/', views.efs_signup, name='efs_signup'),
    path('signup/email_verification/account_activated/', views.efs_account_activated, name='efs_account_activated'),
    path('signup/email_verification/activation_failed/', views.efs_activation_failed, name='efs_activation_failed'),
    path('activate/<uidb64>/<token>', views.efs_activate_account.as_view(), name='efs_activate_account'),
    path('forgot_password/', views.efs_request_reset_email.as_view(), name='efs_request_reset_email'),
    path('forgot_password/reset_email_sent/', views.efs_reset_email_sent, name='efs_reset_email_sent'),
    path('forgot_password/set_password/<uidb64>/<token>', views.efs_change_password.as_view(), name='efs_change_password'),
    path('logout/', views.efs_logout, name='efs_logout'),

    path('resend_activation/<int:user_id>/', views.efs_resend_activation, name='efs_resend_activation'),


    #For answering questions
    path('event_question/<int:event_id>/', views.answer_event_questions, name='answer_event_questions'),
    # For the Custom Dashboard
    path('dashboard/', views.efs_dashboard, name='efs_dashboard'),
    # For Event details
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
]
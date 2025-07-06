from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
# To import account activation token function to create tokens
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.urls import NoReverseMatch, reverse
from .utils import EmailThread
from .utils import generate_unique_username
# reset password generators
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import transaction
# To import settings for sending mail
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
User = get_user_model()
# Import your models
from .models import Event, UserProfile, Attendee

# Import the new combined form and your models
from .forms import CombinedSignupForm, DynamicQuestionsForm 
from .models import Event, UserProfile, Attendee, EventQuestion, AttendeeAnswer


#______________________________________________________________________________
# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages



from django.contrib.auth.decorators import login_required


# ... (your other views) ...

# (Your email sending logic, tokens, etc. should also be imported)
# from .utils import generate_unique_username
# ... etc.

def efs_signup(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        # Pass both request.POST and the event object to the form
        form = CombinedSignupForm(request.POST, event=event)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            try:
                with transaction.atomic():
                    # --- Process STATIC fields to create the user ---
                    username = generate_unique_username(cleaned_data['first_name'])
                    ep_user = User.objects.create_user(
                        username=username,
                        email=cleaned_data['email'],
                        password=cleaned_data['password']
                    )
                    ep_user.first_name = cleaned_data['first_name']
                    ep_user.last_name = cleaned_data['last_name']
                    ep_user.is_active = False  # Deactivate until email verification
                    ep_user.save()

                    # Create the associated UserProfile and Attendee
                    # (Assuming other static fields like company are on the form)
                    UserProfile.objects.create(user=ep_user) # Add other fields here if needed
                    attendee = Attendee.objects.create(user=ep_user, event=event)

                    # --- Process DYNAMIC fields and save answers ---
                    for key, value in cleaned_data.items():
                        if key.startswith('custom_question_'):
                            question_id = int(key.replace('custom_question_', ''))
                            question = EventQuestion.objects.get(id=question_id)
                            
                            answer_value = ", ".join(value) if isinstance(value, list) else str(value)

                            AttendeeAnswer.objects.create(
                                attendee=attendee,
                                question=question,
                                answer=answer_value
                            )

            except Exception as e:
                messages.error(request, f"An error occurred during registration: {e}")
                return redirect('efs_signup', event_id=event.id)
        # --- 4. Send the verification email (your existing logic) ---
            current_site = get_current_site(request)
            mail_subject = 'EFS Team - Verify your email address'
            message = render_to_string('efs_email_activation_message.html', {
                'user': ep_user, 
                'domain': current_site.domain,
                'user_id': urlsafe_base64_encode(force_bytes(ep_user.pk)),
                'token': account_activation_token.make_token(ep_user),
            })
            email_message = EmailMessage(
                mail_subject, message, from_email=settings.DEFAULT_FROM_EMAIL, to=[ep_user.email]
            )
            #EmailThread(email_message).start()
                        
            # EmailThread(email_message).start() # <--- COMMENT THIS OUT
            try:
                email_message.send() # <--- USE THIS INSTEAD FOR DEBUGGING
                messages.info(request, "DEBUG: Email send attempt was successful.")
            except Exception as e:
                # This will now show you the exact error from the email server!
                messages.error(request, f"EMAIL FAILED: {e}")
                return redirect('efs_signup', event_id=event.id) # Stop here if email fails
            
            return redirect('efs_verification_email_sent') # Or your success page

    else:
        # For a GET request, create an unbound form, passing the event
        form = CombinedSignupForm(event=event)

    # --- ADD THIS LINE ---
    # Define a string of your form's static field names, separated by spaces.
    has_dynamic_questions = len(form.fields) > 5
    
    context = {
        'form': form,
        'event': event,
        'has_dynamic_questions':has_dynamic_questions,
    }
    return render(request, 'efs_signup.html', context)


# core/views.py

@login_required
def answer_event_questions(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user = request.user

    # Check if the user is already an attendee for this event
    if Attendee.objects.filter(user=user, event=event).exists():
        messages.info(request, f"You have already registered and answered the questions for '{event.name}'.")
        # Redirect to the user's dashboard or the event detail page
        return redirect('efs_dashboard') 

    if request.method == 'POST':
        form = DynamicQuestionsForm(request.POST, event=event)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Register the user as an attendee
                    attendee = Attendee.objects.create(user=user, event=event)

                    # 2. Save all their answers
                    for key, value in form.cleaned_data.items():
                        if key.startswith('custom_question_'):
                            question_id = int(key.replace('custom_question_', ''))
                            question = EventQuestion.objects.get(id=question_id)
                            answer_value = ", ".join(value) if isinstance(value, list) else str(value)

                            AttendeeAnswer.objects.create(
                                attendee=attendee,
                                question=question,
                                answer=answer_value
                            )
                
                messages.success(request, f"Thank you! Your answers for '{event.name}' have been saved.")
                return redirect('efs_dashboard') # Redirect to a success page

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

    else: # GET request
        form = DynamicQuestionsForm(event=event)

    context = {
        'form': form,
        'event': event,
    }
    # We need a new template for this page
    return render(request, 'efs_answer_questions.html', context)


def efs_verification_email_sent(request):
    return render(request, 'efs_verification_email_sent.html')


# core/views.py

class efs_activate_account(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            if user.is_active:
                # User is ALREADY active. This is not an error.
                messages.info(request, "Your account is already active. Please log in.")
                return redirect('efs_login')
            else:
                # This is the successful activation path.
                user.is_active = True
                user.save()
                return redirect('efs_account_activated')
        
        else:
            # This is the "invalid link" path (bad user or expired token).
            # We will render a helpful "failed" page.
            # We pass the user object if we found one, so we can offer to resend the email.
            context = {'user': user} 
            return render(request, 'efs_activation_failed.html', context)


def efs_account_activated(request):
    return render(request, 'efs_account_activated.html')

def efs_activation_failed(request):
    return render(request, 'efs_activation_failed.html')

# core/views.py

def efs_resend_activation(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('efs_login') # Or some other default page

    if user.is_active:
        messages.info(request, "This account is already active. Please log in.")
        return redirect('efs_login')

    # --- Re-use the email sending logic from your signup view ---
    current_site = get_current_site(request)
    mail_subject = 'EFS Team - Resent: Verify your email address'
    message = render_to_string('efs_email_activation_message.html', {
        'user': user, 
        'domain': current_site.domain,
        'user_id': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    email_message = EmailMessage(
        mail_subject, message, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email]
    )
    EmailThread(email_message).start()

    messages.success(request, f"A new activation email has been sent to {user.email}. Please check your inbox.")
    # Redirect to the same "email sent" confirmation page
    return redirect('efs_verification_email_sent')
 

# core/views.py

def efs_login(request):
    # --- CHANGE 1: REDIRECT IF ALREADY LOGGED IN ---
    # At the very top of the view, check if the user is already authenticated.
    if request.user.is_authenticated:
        # Check for the most privileged roles first.
        if request.user.is_staff:
            return redirect('admin:index')
        else:
            return redirect('efs_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
                
        # --- CHANGE 2: CAPTURE THE 'next' PARAMETER ---
        next_url = request.POST.get('next')

        # Check if a user with that email exists
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid login credentials.')
            return redirect('efs_login')

        # Use the corresponding username to authenticate
        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None and user.is_active:
            login(request, user)

            # --- CHANGE 3: REDIRECT TO 'next' URL IF IT EXISTS AND IS SAFE ---
            # url_has_allowed_host_and_scheme is a security measure to prevent redirecting to malicious sites.
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            # --- NEW, IMPROVED REDIRECTION LOGIC ---
            # Check for the most privileged roles first.
            # 'is_staff' is True for superusers and any other staff members.
            # This is the correct check for "can this user access the admin site?"
            if user.is_staff:
                # Redirect staff and superusers to the Django admin index.
                return redirect('admin:index')
            else:
                # All other active, non-staff users go to the main dashboard.
                return redirect('efs_dashboard')
        
        # This handles cases of wrong password or inactive account
        else:
            messages.error(request, 'Invalid login credentials or account not activated.')
            return redirect('efs_login')

    # For GET requests, just show the login page
    return render(request, 'efs_login.html')



class efs_request_reset_email(View):
    def get(self, request):
        return render(request, 'efs_request_reset_email.html')
    
    def post(self, request):
        reset_email_raw = request.POST.get('email') # Use .get() to avoid errors if email is missing
        reset_email = reset_email_raw.strip().lower() if reset_email_raw else None
        
        # Security Best Practice:
        # Always redirect to a confirmation page, even if the email doesn't exist.
        # This prevents attackers from figuring out which emails are registered.
        
        if reset_email:
            user_queryset = User.objects.filter(email=reset_email)

            if user_queryset.exists():
                user = user_queryset.first() # Get the actual user object
                current_site = get_current_site(request)
                email_subject = 'Reset Your Password'
                
                # IMPORTANT: The URL must point to your NEW password reset view
                # Let's assume you will call its URL 'epusers_reset_password_confirm'
                message = render_to_string('efs_reset_password_message.html', {
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': PasswordResetTokenGenerator().make_token(user),
                    'user': user # Pass the user to the template for personalization
                })

                email_message = EmailMessage(
                    email_subject, 
                    message, 
                    from_email=settings.DEFAULT_FROM_EMAIL, 
                    to=[reset_email]
                )
                EmailThread(email_message).start()

        # Redirect to the "sent" page to complete the process
        return redirect('efs_reset_email_sent')
    
def efs_reset_email_sent(request):
    return render(request, 'efs_reset_email_sent.html')

# The page to handle the click form the email containing the password reset email + The change password form
class efs_change_password(View):
    
    def get(self, request, uidb64, token):
        try:
            # First, try to decode the user ID and find the user
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            # Then, check if the token is valid for that user
            if not PasswordResetTokenGenerator().check_token(user, token):
                # If token is invalid, show a clear error page
                messages.error(request, "This password reset link is invalid or has expired.")
                return redirect('efs_request_reset_email') # Redirect to the start

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            # If the user doesn't exist or uidb64 is bad, treat it as an invalid link
            messages.error(request, "This password reset link is invalid or has expired.")
            return redirect('efs_request_reset_email')

        # If everything is valid, render the form
        context = {
            'uidb64': uidb64,
            'token': token
        }
        # The template name should match your file system
        return render(request, 'efs_change_password.html', context)
    
    def post(self, request, uidb64, token):
        # --- CRITICAL: RE-VALIDATE THE USER AND TOKEN ON POST ---
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.error(request, "This password reset link is invalid or has expired.")
                return redirect('efs_request_reset_email')

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "This password reset link is invalid or has expired.")
            return redirect('efs_request_reset_email')
        
        # --- NOW, PROCEED WITH PASSWORD VALIDATION ---
        new_password = request.POST.get('password')
        confirm_new_password = request.POST.get('confirm_password')

        if new_password != confirm_new_password:
            messages.warning(request, 'Passwords do not match.')
            # We need to re-render the page, passing context so the form URL works
            context = {'uidb64': uidb64, 'token': token}
            return render(request, 'users/efs_change_password.html', context)
        
        # If passwords match, set the new password and save
        user.set_password(new_password)
        user.save()

        messages.success(request, "Your password has been reset successfully! You can now log in.")
        
        # Redirect to the login page
        return redirect('efs_login') # Use the name of your login URL
    

def efs_logout(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('efs_login')

############################################################################################################################
############################################################################################################################
############################################################################################################################
############################################################################################################################



@login_required
def efs_dashboard(request):
    now = timezone.now()

    # --- 1. Get ONGOING events ---
    # An event is ongoing if it has started but has not yet ended.
    ongoing_events = Event.objects.filter(
        is_active=True,
        start_datetime__lte=now,  # The event has started (or started now)
        end_datetime__gte=now     # The event has not yet ended
    ).order_by('start_datetime')


    # --- 2. Get UPCOMING events ---
    # An event is upcoming if it starts in the future.
    upcoming_events = Event.objects.filter(
        is_active=True,
        start_datetime__gt=now    # The event starts after now
    ).order_by('start_datetime')


    # --- 3. Pass BOTH lists to the template ---
    context = {
        'ongoing_events': ongoing_events,
        'upcoming_events': upcoming_events,
        'user': request.user,
    }
    return render(request, 'efs_dashboard.html', context)


def event_detail(request, event_id):
    # Fetch the main event object
    event = get_object_or_404(Event, pk=event_id)

    # Fetch related data efficiently
    sessions = event.sessions.prefetch_related('speakers').all()
    resources = event.resources.filter(is_visible=True)
    
    # Check if the current user is registered for this event
    is_registered = False
    if request.user.is_authenticated:
        is_registered = Attendee.objects.filter(user=request.user, event=event).exists()

    context = {
        'event': event,
        'sessions': sessions,
        'resources': resources,
        'is_registered': is_registered,
    }
    return render(request, 'event_detail.html', context)
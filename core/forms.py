# core/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import EventQuestion, EventResource

class CombinedSignupForm(forms.Form):
    # --- Part 1: Define the STATIC, REQUIRED fields ---
    # These fields will ALWAYS appear on the form.
    first_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Jane'})
    )
    last_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Doe'})
    )
    email = forms.EmailField(
        max_length=254, required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Choose a secure password'})
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )
    
    # You can add other static fields here if you want (e.g., company_name)

# In core/forms.py


    # --- REPLACE YOUR __init__ METHOD WITH THIS ONE ---
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        questions = EventQuestion.objects.filter(event=event)

        for question in questions:
            field_key = f'custom_question_{question.id}'
            choices = [(choice, choice) for choice in question.get_choices_as_list()]
            
            field_class = None
            field_widget = None

            if question.field_type == 'text':
                field_class = forms.CharField
            elif question.field_type == 'textarea':
                field_class = forms.CharField
                field_widget = forms.Textarea
            elif question.field_type == 'dropdown':
                field_class = forms.ChoiceField
                field_widget = forms.Select
            elif question.field_type == 'radio':
                field_class = forms.ChoiceField
                field_widget = forms.RadioSelect
            elif question.field_type == 'checkbox':
                field_class = forms.MultipleChoiceField
                field_widget = forms.CheckboxSelectMultiple
            
            if field_class:
                field_kwargs = {
                    'label': question.label,
                    'required': question.is_required
                }
                if choices:
                    field_kwargs['choices'] = choices
                if field_widget:
                    field_kwargs['widget'] = field_widget

                self.fields[field_key] = field_class(**field_kwargs)
                
                # --- THIS IS THE CRITICAL LOGIC ---
                # It prevents .form-control from being added to radios/checkboxes.
                if question.field_type not in ['radio', 'checkbox']:
                    self.fields[field_key].widget.attrs.update({'class': 'form-control'})

    # ... (your clean methods are here)

    # --- Part 3: Validation Logic ---
    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

# core/forms.py

# ... (all your existing imports and the CombinedSignupForm) ...


# ==============================================================================
# A NEW FORM FOR LOGGED-IN USERS TO ANSWER QUESTIONS
# ==============================================================================
class DynamicQuestionsForm(forms.Form):
    # This form has NO static fields by default.
    # It will be populated entirely by the __init__ method.

    def __init__(self, *args, **kwargs):
        # We re-use the exact same logic from our CombinedSignupForm's initializer.
        # This is efficient and ensures consistency.
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        questions = EventQuestion.objects.filter(event=event)

        for question in questions:
            field_key = f'custom_question_{question.id}'
            choices = [(choice, choice) for choice in question.get_choices_as_list()]
            
            field_class = None
            field_widget = None

            if question.field_type == 'text':
                field_class = forms.CharField
            elif question.field_type == 'textarea':
                field_class = forms.CharField
                field_widget = forms.Textarea
            elif question.field_type == 'dropdown':
                field_class = forms.ChoiceField
                field_widget = forms.Select
            elif question.field_type == 'radio':
                field_class = forms.ChoiceField
                field_widget = forms.RadioSelect
            elif question.field_type == 'checkbox':
                field_class = forms.MultipleChoiceField
                field_widget = forms.CheckboxSelectMultiple
            
            if field_class:
                field_kwargs = {
                    'label': question.label,
                    'required': question.is_required
                }
                if choices:
                    field_kwargs['choices'] = choices
                if field_widget:
                    field_kwargs['widget'] = field_widget

                self.fields[field_key] = field_class(**field_kwargs)
                
                if question.field_type not in ['radio', 'checkbox']:
                    self.fields[field_key].widget.attrs.update({'class': 'form-control'})


class EventResourceForm(forms.ModelForm):
    class Meta:
        model = EventResource
        fields = ['title', 'file', 'is_visible']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'is_visible': 'Check this to make the file available to all event attendees.'
        }
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from import_export.admin import ImportExportModelAdmin # <-- Import this
from import_export import resources 
# Import all your models from the core app
########################
import csv
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
######################
from .models import Event, UserProfile, Attendee, EventQuestion, AttendeeAnswer, Speaker, EventResource, Session

# ==============================================================================
# 1. ADMIN SITE TEXT & TITLE CUSTOMIZATION
# ==============================================================================
admin.site.site_header = "EFS Portal Administration"
admin.site.site_title = "EFS Portal Admin"
admin.site.index_title = "Welcome to the EFS Portal"



# --- Add this new SessionInline class ---
class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    fields = ('start_time', 'end_time', 'title', 'speakers')
    # Use a better widget for selecting speakers
    filter_horizontal = ('speakers',)



# ==============================================================================
# NEW: EVENT RESOURCE INLINE
# ==============================================================================
class EventResourceInline(admin.TabularInline):
    model = EventResource
    extra = 1 # Allow adding one new resource at a time
    fields = ('title', 'speaker', 'file', 'is_visible')
    # Pre-populate the speaker choices based on speakers already assigned to the event
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "speaker":
            # Get the event object being edited
            event_id = request.resolver_match.kwargs.get('object_id')
            if event_id:
                event = Event.objects.get(pk=event_id)
                kwargs["queryset"] = event.speakers.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)




# 1. Create a "Resource" to describe how the Attendee model maps to an export
class AttendeeResource(resources.ModelResource):
    class Meta:
        model = Attendee
        # Define which fields you want in the export
        fields = ('id', 'user__first_name', 'user__last_name', 'user__email', 'event__name', 'registration_date')
        export_order = fields

# ==============================================================================
# 2. USER AND USERPROFILE ADMIN (This section is already excellent)
# ==============================================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email') # <-- IMPROVEMENT: Added search
    actions = ['activate_users']

    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} users were successfully activated.')
    activate_users.short_description = "Activate selected users"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ==============================================================================
# 3. EVENT ADMIN with DYNAMIC FORM BUILDER
# ==============================================================================

class EventQuestionInline(admin.TabularInline):
    model = EventQuestion
    extra = 1
    fields = ('order', 'label', 'field_type', 'choices', 'is_required')
    ordering = ('order',)
    verbose_name = "Custom Form Field"
    verbose_name_plural = "Custom Form Fields"



@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user') # Show the name and linked user (if any)
    search_fields = ('name', 'user__username', 'user__email')
    list_filter = ('events',) # Allow filtering by events they are speaking at



@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # --- IMPROVED ---
    list_display = ('name', 'start_datetime', 'end_datetime', 'is_active', 'event_status', 'attendee_count')
    list_filter = ('is_active', 'start_datetime') # Filter by the new field
    search_fields = ('name',)
    # --- NEW, IMPROVED WIDGET FOR SELECTING SPEAKERS ---
     # --- ADD THE NEW SESSION INLINE HERE ---
    inlines = [EventQuestionInline, EventResourceInline, SessionInline]
    filter_horizontal = ('speakers',) # This is for the main event speakers
    
    # Automatically set the 'uploaded_by' field for resources added in the admin
    def save_formset(self, request, form, formset, change):
        if formset.model == EventResource:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk: # If it's a new object
                    instance.uploaded_by = request.user
                instance.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)
    
    
    # This makes the property sortable in the admin (optional but nice)
    @admin.display(description='Status', ordering='start_datetime')
    def event_status(self, obj):
        return obj.event_status


    def attendee_count(self, obj):
        """Custom method to count attendees, using the new related_name."""
        return obj.attendees.count()
    attendee_count.short_description = 'Registered Attendees'


# ==============================================================================
# 4. ATTENDEE ADMIN with CUSTOM ANSWERS
# ==============================================================================

class AttendeeAnswerInline(admin.TabularInline):
    model = AttendeeAnswer
    extra = 0
    readonly_fields = ('question', 'answer')
    can_delete = False


@admin.register(Attendee)
class AttendeeAdmin(ImportExportModelAdmin):
    resource_class = AttendeeResource
    # --- IMPROVED ---
    list_display = ('user_email', 'event', 'registration_date')
    list_filter = ('event',)
    search_fields = ('user__email', 'user__username', 'event__name')
    date_hierarchy = 'registration_date' # Adds a date drill-down navigation
    list_select_related = ('user', 'event') # Performance optimization
    inlines = [AttendeeAnswerInline]

    def user_email(self, obj):
        """Helper method to display the user's email, which is more useful."""
        return obj.user.email
    user_email.short_description = 'User Email' # Sets the column header text


# In core/admin.py

class AttendeeAnswerInlineForQuestion(admin.TabularInline):
    model = AttendeeAnswer
    extra = 0  # We don't want to add new answers here, just view them.
    
    # Show who answered and what they said. These fields should not be editable here.
    readonly_fields = ('attendee_user', 'answer', 'registration_date')
    
    # We don't want to allow deleting answers from this view.
    can_delete = False

    def attendee_user(self, obj):
        """A helper to display the attendee's name and email for clarity."""
        return f"{obj.attendee.user.get_full_name()} ({obj.attendee.user.email})"
    attendee_user.short_description = 'Attendee'

    def registration_date(self, obj):
        """Shows when the attendee registered."""
        return obj.attendee.registration_date.strftime("%Y-%m-%d %H:%M")
    registration_date.short_description = 'Answered On'

    # Improve performance by pre-fetching related user data
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('attendee__user')
    
# In core/admin.py

@admin.register(EventQuestion)
class EventQuestionAdmin(admin.ModelAdmin):
    # What to show in the main list view of questions
    list_display = ('label', 'event', 'field_type', 'is_required', 'response_count')
    
    # --- ADD THE ACTIONS ---
    actions = ['export_summary_as_csv', 'export_summary_as_pdf']
    
    # Allow filtering by event and field type
    list_filter = ('event', 'field_type', 'is_required')
    
    # Allow searching by the question text or the event name
    search_fields = ('label', 'event__name')

    # This is the key part: show the answers inline
    inlines = [AttendeeAnswerInlineForQuestion]


    def _get_summary_data(self, question):
        """Helper method to get the aggregated data."""
        from django.db.models import Count
        return AttendeeAnswer.objects.filter(
            question=question
        ).values(
            'answer'
        ).annotate(
            count=Count('answer')
        ).order_by(
            '-count'
        )

    def export_summary_as_csv(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one question to export.", level='warning')
            return
        
        question = queryset.first()
        summary_data = self._get_summary_data(question)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{question.label}_summary.csv"'

        writer = csv.writer(response)
        writer.writerow(['Answer', 'Count']) # Header row

        for item in summary_data:
            writer.writerow([item['answer'], item['count']])

        return response
    export_summary_as_csv.short_description = "Export Summary as CSV (Excel)"

    def export_summary_as_pdf(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one question to export.", level='warning')
            return

        question = queryset.first()
        summary_data = self._get_summary_data(question)

        context = {
            'question': question,
            'summary_data': summary_data,
            'total_responses': sum(item['count'] for item in summary_data)
        }
        
        # Render our HTML template
        html_string = render_to_string('admin/question_summary_report.html', context)
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{question.label}_summary.pdf"'
        return response
    export_summary_as_pdf.short_description = "Export Summary as PDF"

    # ... (the rest of your EventQuestionAdmin code) ...
    
    # A helper method to quickly see how many responses a question has
    def response_count(self, obj):
        return obj.responses.count()
    response_count.short_description = 'No. of Responses'
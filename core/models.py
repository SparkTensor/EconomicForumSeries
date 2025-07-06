from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone # <-- ADD THIS IMPORT
from django.templatetags.static import static
from django.urls import reverse

# ==============================================================================
# 1. Event Model
# Stores the core details for each event.
# ==============================================================================
class Event(models.Model):
    # --- NEW: EVENT TYPE CHOICES ---
    class EventType(models.TextChoices):
        PHYSICAL = 'Physical', 'Physical'
        ONLINE = 'Online', 'Online'
        HYBRID = 'Hybrid', 'Hybrid'
    
    name = models.CharField(max_length=200)
    # --- MODIFIED/RENAMED and NEW DATE FIELDS ---
    start_datetime = models.DateTimeField(help_text="The date and time the event starts.")
    end_datetime = models.DateTimeField(
        help_text="The date and time the event ends.",
        blank=True, # Make it optional, as some events might be single points in time
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date the event was created in the system.")
        
    # --- NEW: TYPE AND LOCATION FIELDS ---
    event_type = models.CharField(
        max_length=10,
        choices=EventType.choices,
        default=EventType.PHYSICAL,
        help_text="The format of the event."
    )
    physical_location = models.CharField(
        max_length=255,
        blank=True,
        help_text="The address or venue for physical or hybrid events."
    )
    online_link = models.URLField(
        max_length=255,
        blank=True,
        help_text="The meeting/stream link for online or hybrid events."
    )

    description = models.TextField(blank=True, help_text="Optional: A detailed description of the event.")
    is_active = models.BooleanField(default=True, help_text="Uncheck this to hide the event from public view.")
    # --- NEW FIELD ---
    speakers = models.ManyToManyField(
        'Speaker', 
        blank=True, 
        related_name='events',
        help_text="Select speakers for this event."
    )
    # --- NEW FIELD FOR EVENT IMAGE ---
    featured_image = models.ImageField(
        upload_to='event_images/',
        blank=True,
        null=True,
        help_text="A featured image for the event, displayed on home/list pages."
    )

    class Meta:
        # --- UPDATE ORDERING ---
        ordering = ['start_datetime']
        verbose_name = "Event"
        verbose_name_plural = "Events"

       
    # --- THIS IS THE NEW, CORRECT WAY TO PROVIDE A DEFAULT ---
    @property
    def featured_image_url(self):
        """
        Returns the URL for the event's featured image.
        If no image is uploaded, it returns the URL for a default static image.
        """
        if self.featured_image:
            return self.featured_image.url
        else:
            # This will correctly return '/static/images/default_event.png'
            return static('images/default.png')

    def __str__(self):
        return self.name
    
        
    # --- NEW: COMPUTED PROPERTIES FOR STATUS ---
    @property
    def event_status(self):
        """
        Returns the status of the event as a string: 
        'Past', 'Ongoing', or 'Upcoming'.
        """
        now = timezone.now()
        # If the event has a defined end time and it's in the past
        if self.end_datetime and self.end_datetime < now:
            return 'Past'
        # If the event start time is in the future
        if self.start_datetime > now:
            return 'Upcoming'
        # If it's not in the future and not in the past, it must be ongoing
        else:
            return 'Ongoing'

    @property
    def is_past(self):
        """A simple boolean check, very useful in templates."""
        return self.event_status == 'Past'
    
    
    def get_absolute_url(self):
        """Returns the canonical URL for an event detail page."""
        return reverse('event_detail', kwargs={'event_id': self.pk})
    

# ==============================================================================
# 6. EventResource Model (NEW)
# Represents a single file (PDF, slides, etc.) uploaded for an event.
# ==============================================================================
class EventResource(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='resources')
    speaker = models.ForeignKey('Speaker', on_delete=models.CASCADE, related_name='resources')
    
    title = models.CharField(max_length=200, help_text="A user-friendly title for the resource.")
    file = models.FileField(upload_to='event_resources/', help_text="The uploaded file (PDF, PPT, image, etc.).")
    
    # --- VISIBILITY AND AUDITING FIELDS ---
    is_visible = models.BooleanField(
        default=False, 
        help_text="Check this box to make the resource visible to public attendees."
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_resources',
        help_text="The user account that performed the upload."
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event', 'speaker', 'title']
        verbose_name = "Event Resource"
        verbose_name_plural = "Event Resources"

    def __str__(self):
        return f'"{self.title}" for {self.event.name} by {self.speaker.name}'

    

# 2. Speaker Model (NEW)
# Stores details for a speaker. Can be linked to a User or be standalone.
# ==============================================================================
class Speaker(models.Model):
    name = models.CharField(max_length=200, help_text="The speaker's full name.")
    bio = models.TextField(help_text="A short biography of the speaker.")
    picture = models.ImageField(
        upload_to='speakers/', 
        blank=True, 
        null=True, 
        help_text="A headshot or profile picture for the speaker."
    )
    
    # --- THIS IS THE KEY ---
    # Optional link to a registered user in the system.
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # If the user is deleted, don't delete the speaker profile
        null=True,
        blank=True,
        related_name='speaker_profile',
        help_text="(Optional) Link this speaker to a registered user account."
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Speaker"
        verbose_name_plural = "Speakers"

     # --- THIS IS THE NEW, CORRECT WAY TO PROVIDE A DEFAULT ---
    @property
    def picture_url(self):
        """
        Returns the URL for the event's featured image.
        If no image is uploaded, it returns the URL for a default static image.
        """
        if self.picture:
            return self.picture.url
        else:
            # This will correctly return '/static/images/default_event.png'
            return static('images/default.png')

    def __str__(self):
        return self.name



# ==============================================================================
# 2. UserProfile Model
# Extends the default User model with your application-specific fields.
# ==============================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    # Add other profile fields here if needed
        
    # --- ADD NEW FIELDS HERE ---
    linkedin_profile = models.URLField(max_length=255, blank=True, help_text="e.g., https://linkedin.com/in/yourname")
    website = models.URLField(max_length=255, blank=True, help_text="Your personal or company website.")
    professional_interests = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Comma-separated interests, e.g., AI, Marketing, Fintech"
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile for {self.user.username}"


# ==============================================================================
# 3. Attendee Model
# The "linking table" that registers a User for a specific Event.
# ==============================================================================
class Attendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event') # Prevents a user from registering for the same event twice.
        ordering = ['-registration_date']
        verbose_name = "Attendee"
        verbose_name_plural = "Attendees"

    def __str__(self):
        return f'{self.user.username} attending {self.event.name}'


# ==============================================================================
# 4. EventQuestion Model (For the Dynamic Form Builder)
# Stores a single question created by an admin for an event's form.
# ==============================================================================
class EventQuestion(models.Model):
    FIELD_TYPE_CHOICES = [
        ('text', 'Text (Single Line)'),
        ('textarea', 'Text (Multi-Line)'),
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes (Multiple Answers)'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='questions')
    label = models.CharField(max_length=255, help_text="The question text that the user will see.")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    is_required = models.BooleanField(default=False)
    choices = models.TextField(
        blank=True,
        help_text="For Dropdown, Radio, or Checkbox fields. Enter one choice per line."
    )
    order = models.PositiveIntegerField(default=0, help_text="The order in which the question will appear on the form.")

    class Meta:
        ordering = ['order']
        verbose_name = "Event Question"
        verbose_name_plural = "Event Questions"

    def __str__(self):
        return f'"{self.label}" for event: {self.event.name}'
    
    def get_choices_as_list(self):
        """Helper method to convert the text choices into a list."""
        return [choice.strip() for choice in self.choices.splitlines() if choice.strip()]


# ==============================================================================
# 5. AttendeeAnswer Model (For the Dynamic Form Builder)
# Stores a user's answer to a single custom EventQuestion.
# ==============================================================================
class AttendeeAnswer(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(EventQuestion, on_delete=models.CASCADE, related_name='responses')
    answer = models.TextField(blank=True)

    class Meta:
        verbose_name = "Attendee Answer"
        verbose_name_plural = "Attendee Answers"

    def __str__(self):
        return f'Answer by {self.attendee.user.username} for "{self.question.label}"'

# 7. Session Model (NEW)
# Represents a single scheduled item within an event's agenda.
# ==============================================================================
class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    speakers = models.ManyToManyField(
        Speaker, 
        blank=True, 
        related_name='sessions',
        help_text="Speakers for this specific session."
    )

    class Meta:
        ordering = ['start_time']
        verbose_name = "Event Session"
        verbose_name_plural = "Event Sessions"

    def __str__(self):
        return f'"{self.title}" at {self.event.name}'
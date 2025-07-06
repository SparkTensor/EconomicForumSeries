import threading
from django.contrib.auth import get_user_model
from django.utils.text import slugify

# To get the user - even if it's a custom model with any name.
User = get_user_model()

class EmailThread(threading.Thread):
    def __init__(self, email_message):
        super().__init__()
        self.email_message = email_message
    def run(self):
        self.email_message.send()


# To create unique username from the first name of a user
def generate_unique_username(first_name):
    # Use 'user' as a fallback if first_name is empty
    if not first_name:
        base_username = "user"
    else:
        # slugify is great for creating clean usernames from names
        base_username = slugify(first_name)

    username = base_username
    counter = 1
    # Loop until we find a username that does not exist
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username
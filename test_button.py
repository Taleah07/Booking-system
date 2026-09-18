import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Get or create the staff user
user = User.objects.get(username='taleah')
user.is_staff = True
user.is_superuser = True
user.save()

# Create a test client and log in
client = Client()
client.force_login(user)

# Make a request to the technical page
response = client.get('/technical/', HTTP_HOST='127.0.0.1:8000')
content = response.content.decode()

# Check if the button is in the response
button_present = 'toggleEditBtn' in content
enable_editing_present = 'Enable Editing' in content
bookings_link_present = 'Bookings' in content

print(f"Toggle Edit Button ID Present: {button_present}")
print(f"Enable Editing Text Present: {enable_editing_present}")
print(f"Bookings Link Present: {bookings_link_present}")

# Also check for the JavaScript function
toggle_function_present = 'function toggleEditMode()' in content
print(f"toggleEditMode Function Present: {toggle_function_present}")

# Print first occurrence of toggleEditBtn to verify it's correctly rendered
if button_present:
    idx = content.find('toggleEditBtn')
    print(f"\nContext around toggleEditBtn:\n{content[max(0, idx-100):idx+200]}")

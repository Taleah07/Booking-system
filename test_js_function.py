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

# Check for key components
has_edit_links = '.edit-links' in content
has_header_controls = '.header-controls' in content
has_toggle_function = 'function toggleEditMode()' in content

# Check the implementation
if has_toggle_function:
    idx = content.find('function toggleEditMode()')
    snippet = content[idx:idx+500]
    print("JavaScript function found:")
    print(snippet)
    print("\n" + "="*60 + "\n")
    
    # Check if it's targeting the right selectors
    print(f"Targets '.edit-links': {'edit-links' in snippet}")
    print(f"Targets '.header-controls': {'header-controls' in snippet}")
    print(f"Uses 'forEach': {'forEach' in snippet}")
    print(f"Sets display to 'flex': {'display' in snippet and 'flex' in snippet}")
else:
    print("ERROR: toggleEditMode function not found!")

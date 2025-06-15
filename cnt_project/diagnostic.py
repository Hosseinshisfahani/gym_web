#!/usr/bin/env python3

import os
import sys

print("=== Django Diagnostic Script ===")

# Check Django installation
try:
    import django
    print(f"✓ Django installed: {django.get_version()}")
except ImportError as e:
    print(f"✗ Django not installed: {e}")
    sys.exit(1)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_website.settings')

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

# Check database connection
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")

# Check if models can be loaded
try:
    from gym.models import UserProfile, WorkoutPlan, DietPlan, Payment, Ticket
    print("✓ Models loaded successfully")
except Exception as e:
    print(f"✗ Models loading failed: {e}")

# Check if admin can be loaded
try:
    from gym.admin import admin_site
    print("✓ Admin site loaded successfully")
except Exception as e:
    print(f"✗ Admin site loading failed: {e}")

# Check if URLs can be loaded
try:
    from django.urls import reverse
    from django.test import RequestFactory
    from gym import views
    
    # Test a simple URL resolution
    home_url = reverse('gym:home')
    print(f"✓ URL resolution working: {home_url}")
except Exception as e:
    print(f"✗ URL resolution failed: {e}")

print("\n=== Environment Info ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")

print("\n=== Django Settings Check ===")
try:
    from django.conf import settings
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"Database: {settings.DATABASES['default']['ENGINE']}")
    print(f"Database Name: {settings.DATABASES['default']['NAME']}")
    print(f"Static URL: {settings.STATIC_URL}")
    print(f"Static Root: {settings.STATIC_ROOT}")
except Exception as e:
    print(f"✗ Settings check failed: {e}")

print("\n=== Diagnostic Complete ===") 
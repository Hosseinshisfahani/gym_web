# Google OAuth Setup Guide for Gym Website

## Overview
This guide will help you set up Google OAuth authentication for your Django gym website using django-allauth.

## Prerequisites
- Django project with django-allauth installed
- Google Cloud Console account
- Domain name configured (shirneshansport.ir)

## Step 1: Google Cloud Console Setup

### 1.1 Create/Select Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### 1.2 Enable Google+ API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API" and enable it
3. Also enable "Google OAuth2 API" if not already enabled

### 1.3 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application" as the application type
4. Set the name (e.g., "Gym Website OAuth")
5. Add authorized redirect URIs:
   - **Development**: `http://127.0.0.1:8000/accounts/google/login/callback/`
   - **Production**: `https://shirneshansport.ir/accounts/google/login/callback/`
6. Click "Create"
7. Copy the **Client ID** and **Client Secret**

## Step 2: Environment Configuration

### 2.1 Update .env File
Edit `/home/gym_web/cnt_project/.env` and replace the placeholder values:

```bash
# Replace these with your actual values from Google Cloud Console
GOOGLE_CLIENT_ID=your-actual-google-client-id-here
GOOGLE_CLIENT_SECRET=your-actual-google-client-secret-here

# Also update these for production
DJANGO_SECRET_KEY=your-secure-secret-key-here
DOMAIN=shirneshansport.ir
```

### 2.2 Security Notes
- Never commit the `.env` file to version control
- Use strong, unique values for `DJANGO_SECRET_KEY`
- Keep your Google OAuth credentials secure

## Step 3: Django Configuration Verification

### 3.1 Check Settings
The following settings are already configured in `settings.py`:

```python
# Allauth apps
INSTALLED_APPS = [
    # ... other apps
    "allauth",
    "allauth.account", 
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Google OAuth provider configuration
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["openid", "email", "profile"],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": False,
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "key": "",
        }
    }
}
```

### 3.2 URL Configuration
The allauth URLs are already included in `urls.py`:
```python
path('accounts/', include('allauth.urls')),
```

## Step 4: Database Migration

Run the following commands to ensure all allauth tables are created:

```bash
cd /home/gym_web
source venv/bin/activate
cd cnt_project
python manage.py migrate
```

## Step 5: Create Google Social Application

### 5.1 Using Django Admin
1. Start the development server: `python manage.py runserver`
2. Go to `http://127.0.0.1:8000/admin/`
3. Login with your superuser account
4. Go to "Sites" > "Sites" and add/verify your domain
5. Go to "Social Applications" > "Social Applications" > "Add social application"
6. Fill in:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: (from your .env file)
   - **Secret key**: (from your .env file)
   - **Sites**: Select your site (shirneshansport.ir)

### 5.2 Using Django Shell (Alternative)
```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Get or create the site
site = Site.objects.get_or_create(domain='shirneshansport.ir', name='Gym Website')[0]

# Create Google social app
google_app = SocialApp.objects.create(
    provider='google',
    name='Google OAuth',
    client_id='your-google-client-id-here',
    secret='your-google-client-secret-here'
)
google_app.sites.add(site)
```

## Step 6: Testing

### 6.1 Development Testing
1. Start the server: `python manage.py runserver`
2. Go to `http://127.0.0.1:8000/accounts/login/`
3. You should see a "Login with Google" button
4. Click it and test the OAuth flow

### 6.2 Production Testing
1. Deploy your application
2. Go to `https://shirneshansport.ir/accounts/login/`
3. Test the Google OAuth flow

## Step 7: Frontend Integration

### 7.1 Login Template
Add Google login button to your login template:

```html
<!-- In your login template -->
<a href="{% url 'google_login' %}" class="btn btn-google">
    <i class="fab fa-google"></i> Login with Google
</a>
```

### 7.2 Registration Template
Add Google registration button to your registration template:

```html
<!-- In your registration template -->
<a href="{% url 'google_login' %}" class="btn btn-google">
    <i class="fab fa-google"></i> Continue with Google
</a>
```

## Troubleshooting

### Common Issues

1. **"Invalid client" error**
   - Check that your Client ID and Secret are correct
   - Verify the redirect URI matches exactly

2. **"Redirect URI mismatch" error**
   - Ensure the redirect URI in Google Console matches your Django URLs
   - Check both development and production URLs

3. **"Access blocked" error**
   - Verify your domain is added to authorized domains in Google Console
   - Check if your app is in testing mode (add test users)

4. **Database errors**
   - Run `python manage.py migrate` to ensure all tables exist
   - Check that the Social Application is created in admin

5. **"MultipleObjectsReturned" error**
   - This is a known bug in some versions of django-allauth
   - The project includes a custom adapter fix in `gym/adapters.py`
   - If you encounter this error, ensure `SOCIALACCOUNT_ADAPTER` is set in settings

### Debug Mode
Enable debug logging in settings.py for troubleshooting:

```python
LOGGING = {
    # ... existing config
    'loggers': {
        'allauth': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',  # Change from WARNING to DEBUG
            'propagate': False,
        },
    },
}
```

## Security Considerations

1. **HTTPS Required**: Google OAuth requires HTTPS in production
2. **Domain Verification**: Verify your domain in Google Console
3. **Secret Management**: Never expose OAuth secrets in client-side code
4. **Token Security**: Allauth handles token security automatically

## Next Steps

After successful setup:
1. Customize the OAuth flow UI/UX
2. Add additional user profile fields if needed
3. Implement proper error handling
4. Set up monitoring and logging
5. Test thoroughly before production deployment

## Support

If you encounter issues:
1. Check the Django logs: `tail -f debug.log`
2. Verify all environment variables are set correctly
3. Test with a simple Django project first
4. Check Google Cloud Console for any restrictions or errors

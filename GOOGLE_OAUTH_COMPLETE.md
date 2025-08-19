# Google OAuth Setup - COMPLETED ✅

## What Has Been Done

✅ **Dependencies Installed**
- django-allauth==0.60.1
- requests==2.31.0

✅ **Django Settings Updated**
- Added allauth apps to INSTALLED_APPS
- Added allauth middleware
- Configured authentication backends
- Set up allauth settings for Google OAuth

✅ **URLs Configured**
- Added allauth URLs to main URL configuration

✅ **Templates Created**
- Custom login template with Google Sign-In button
- Custom signup template with Google Sign-In button
- Styled Google provider list template
- Base template for account pages

✅ **Admin Configuration**
- Added allauth models to admin interface
- Created management command for OAuth setup

✅ **Database Migrations**
- All allauth tables created successfully
- Site model configured

✅ **Site Configuration**
- Site domain set to: shirneshansport.ir
- Site name set to: Shirneshan Sport

## Next Steps to Complete Setup

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API or Google Identity API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Name: "Shirneshan Sport Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:8000` (development)
     - `https://shirneshansport.ir` (production)
     - `http://shirneshansport.ir` (production)
   - Authorized redirect URIs:
     - `http://localhost:8000/accounts/google/login/callback/` (development)
     - `https://shirneshansport.ir/accounts/google/login/callback/` (production)
     - `http://shirneshansport.ir/accounts/google/login/callback/` (production)

### 2. Configure Google OAuth in Django

**Option A: Using Management Command (Recommended)**
```bash
cd gym_web/cnt_project
source ../venv/bin/activate
python manage.py setup_google_oauth \
    --client-id="YOUR_GOOGLE_CLIENT_ID" \
    --client-secret="YOUR_GOOGLE_CLIENT_SECRET" \
    --domain="shirneshansport.ir"
```

**Option B: Using Django Admin**
1. Start your Django server:
   ```bash
   python manage.py runserver
   ```
2. Go to: `http://localhost:8000/admin/`
3. Navigate to "Social Applications"
4. Create a new social application:
   - Provider: `Google`
   - Name: `Google`
   - Client ID: Your Google Client ID
   - Secret key: Your Google Client Secret
   - Sites: Add your site (shirneshansport.ir)

### 3. Test the Setup

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to: `http://localhost:8000/accounts/login/`

3. You should see:
   - A "Continue with Google" button
   - Regular email/password login form
   - Link to sign up page

4. Test the OAuth flow by clicking the Google button

### 4. Production Deployment

For production, make sure to:

1. **Update Google OAuth credentials** with production domain
2. **Set environment variables** for sensitive data:
   ```bash
   export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
   export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
   ```
3. **Update settings.py** to use environment variables:
   ```python
   import os
   GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
   GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
   ```
4. **Set DEBUG = False** in production settings
5. **Configure SSL certificates** for HTTPS
6. **Update ALLOWED_HOSTS** in settings

## Available URLs

Once configured, these URLs will be available:

- **Login**: `/accounts/login/`
- **Signup**: `/accounts/signup/`
- **Logout**: `/accounts/logout/`
- **Password Reset**: `/accounts/password/reset/`
- **Email Confirmation**: `/accounts/confirm-email/`

## Customization Options

### 1. Customize User Profile Creation

You can customize how user profiles are created when users sign in with Google by creating a custom adapter:

```python
# gym/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Add custom logic here
        return user
```

### 2. Add More Social Providers

To add more providers (Facebook, Twitter, etc.):

1. Add provider to INSTALLED_APPS:
   ```python
   'allauth.socialaccount.providers.facebook',
   'allauth.socialaccount.providers.twitter',
   ```

2. Configure in settings.py:
   ```python
   SOCIALACCOUNT_PROVIDERS = {
       'google': { ... },
       'facebook': {
           'METHOD': 'oauth2',
           'SCOPE': ['email', 'public_profile'],
           'FIELDS': ['id', 'email', 'name', 'first_name', 'last_name'],
       },
   }
   ```

### 3. Customize Templates

All templates can be customized by creating them in:
- `front_end/templates/account/` - for account templates
- `front_end/templates/socialaccount/` - for social account templates

## Troubleshooting

### Common Issues:

1. **"Invalid redirect URI"**
   - Check that redirect URIs in Google Console match exactly
   - Include both HTTP and HTTPS versions

2. **"Client ID not found"**
   - Verify Client ID is set correctly in Django admin
   - Check that site is associated with social application

3. **Template errors**
   - Ensure all template files are in correct locations
   - Check that base template extends correctly

### Debug Commands:

```bash
# Check Django configuration
python manage.py check

# List all URLs
python manage.py show_urls

# Check social applications
python manage.py shell -c "from allauth.socialaccount.models import SocialApp; print(SocialApp.objects.all())"
```

## Security Notes

- ✅ Never commit Client Secret to version control
- ✅ Use environment variables for sensitive data
- ✅ Regularly rotate OAuth credentials
- ✅ Monitor OAuth usage in Google Cloud Console
- ✅ Enable HTTPS in production

## Support

If you encounter issues:

1. Check the detailed setup guide: `GOOGLE_OAUTH_SETUP.md`
2. Review Django allauth documentation
3. Check Google OAuth documentation
4. Verify all URLs and settings are correct

---

**🎉 Congratulations! Your Django project is now ready for Google OAuth integration!**

Just follow the "Next Steps" above to complete the setup with your actual Google OAuth credentials. 
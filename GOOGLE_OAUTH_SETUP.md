# Google OAuth Setup Guide

This guide will help you set up Google Sign-In (OAuth) for your Django gym website.

## Prerequisites

- A Google account
- Access to Google Cloud Console
- Your Django project running

## Step 1: Set Up Google Cloud Console

### 1.1 Create a New Project or Select Existing One

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Make sure the project is selected in the top navigation

### 1.2 Enable Google+ API

1. Go to "APIs & Services" > "Library"
2. Search for "Google+ API" or "Google Identity"
3. Click on it and press "Enable"

### 1.3 Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen first:
   - User Type: External (or Internal if you have Google Workspace)
   - App name: "Shirneshan Sport"
   - User support email: Your email
   - Developer contact information: Your email
   - Save and continue

4. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: "Shirneshan Sport Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:8000` (for development)
     - `https://shirneshansport.ir` (for production)
     - `http://shirneshansport.ir` (for production)
   - Authorized redirect URIs:
     - `http://localhost:8000/accounts/google/login/callback/` (for development)
     - `https://shirneshansport.ir/accounts/google/login/callback/` (for production)
     - `http://shirneshansport.ir/accounts/google/login/callback/` (for production)

5. Click "Create"
6. **Save the Client ID and Client Secret** - you'll need these for the next steps

## Step 2: Install Dependencies

Run the following command to install the required packages:

```bash
cd gym_web/cnt_project
pip install -r requirements.txt
```

## Step 3: Run Database Migrations

```bash
python manage.py migrate
```

## Step 4: Configure Google OAuth

### Option A: Using Management Command (Recommended)

```bash
python manage.py setup_google_oauth \
    --client-id="YOUR_GOOGLE_CLIENT_ID" \
    --client-secret="YOUR_GOOGLE_CLIENT_SECRET" \
    --domain="shirneshansport.ir"
```

### Option B: Using Django Admin

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to your admin panel: `http://localhost:8000/admin/`

3. Navigate to "Sites" and create/update the site:
   - Domain: `shirneshansport.ir`
   - Display name: `Shirneshan Sport`

4. Navigate to "Social Applications" and create a new one:
   - Provider: `Google`
   - Name: `Google`
   - Client ID: Your Google Client ID
   - Secret key: Your Google Client Secret
   - Sites: Add your site

## Step 5: Test the Setup

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to: `http://localhost:8000/accounts/login/`

3. You should see a "Continue with Google" button

4. Click the button and test the OAuth flow

## Step 6: Production Configuration

For production, make sure to:

1. Update your Google OAuth credentials with the production domain
2. Set `DEBUG = False` in your settings
3. Configure proper SSL certificates
4. Update `ALLOWED_HOSTS` in settings
5. Set secure cookie settings

## Troubleshooting

### Common Issues:

1. **"Invalid redirect URI" error**
   - Make sure the redirect URI in Google Console matches exactly
   - Include both HTTP and HTTPS versions for production

2. **"Client ID not found" error**
   - Verify the Client ID is correctly set in Django admin
   - Check that the site is associated with the social application

3. **"Site not found" error**
   - Make sure the site is created in Django admin
   - Verify the site ID matches `SITE_ID = 1` in settings

4. **Template errors**
   - Make sure all template files are in the correct locations
   - Check that the base template extends correctly

### Debug Mode

If you're having issues, you can enable debug mode in your Google OAuth settings:

1. Go to Google Cloud Console
2. Navigate to "APIs & Services" > "OAuth consent screen"
3. Add your email as a test user

## Security Notes

- Never commit your Client Secret to version control
- Use environment variables for sensitive data in production
- Regularly rotate your OAuth credentials
- Monitor OAuth usage in Google Cloud Console

## Additional Features

Once Google OAuth is working, you can:

1. Add more social providers (Facebook, Twitter, etc.)
2. Customize the user profile creation process
3. Add email verification workflows
4. Implement account linking features

## Support

If you encounter any issues:

1. Check the Django allauth documentation
2. Review Google OAuth documentation
3. Check the Django debug logs
4. Verify all URLs and settings are correct 
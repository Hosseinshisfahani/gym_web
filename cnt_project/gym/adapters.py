"""
Custom adapters for django-allauth to fix the MultipleObjectsReturned bug
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.core.exceptions import MultipleObjectsReturned


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that fixes the MultipleObjectsReturned bug in allauth
    """
    
    def get_app(self, request, provider, client_id=None):
        """
        Override get_app to handle the MultipleObjectsReturned bug
        """
        try:
            return super().get_app(request, provider, client_id=client_id)
        except MultipleObjectsReturned:
            # If we get MultipleObjectsReturned, try to get the first app
            from django.contrib.sites.shortcuts import get_current_site
            current_site = get_current_site(request)
            
            apps = SocialApp.objects.filter(provider=provider, sites=current_site)
            if client_id:
                apps = apps.filter(client_id=client_id)
            
            if apps.exists():
                return apps.first()
            else:
                # Fallback to any app with this provider
                apps = SocialApp.objects.filter(provider=provider)
                if client_id:
                    apps = apps.filter(client_id=client_id)
                if apps.exists():
                    return apps.first()
                else:
                    raise SocialApp.DoesNotExist(f"No social app found for provider {provider}")

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.provider import GoogleProvider


class Command(BaseCommand):
    help = 'Set up Google OAuth configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth Client ID',
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Google OAuth Client Secret',
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='shirneshansport.ir',
            help='Domain name for the site',
        )

    def handle(self, *args, **options):
        # Set up the site
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': options['domain'],
                'name': 'Shirneshan Sport',
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created site: {site.domain}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Site already exists: {site.domain}')
            )

        # Set up Google OAuth app
        if options['client_id'] and options['client_secret']:
            social_app, created = SocialApp.objects.get_or_create(
                provider=GoogleProvider.id,
                defaults={
                    'name': 'Google',
                    'client_id': options['client_id'],
                    'secret': options['client_secret'],
                }
            )
            
            if not created:
                social_app.client_id = options['client_id']
                social_app.secret = options['client_secret']
                social_app.save()
                self.stdout.write(
                    self.style.SUCCESS('Updated Google OAuth configuration')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Created Google OAuth configuration')
                )
            
            # Add the site to the social app
            social_app.sites.add(site)
            
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please provide --client-id and --client-secret arguments'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    'You can also configure Google OAuth through the admin interface'
                )
            ) 
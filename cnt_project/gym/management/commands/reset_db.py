from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Reset the database and create a superuser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', 
            default='admin', 
            help='Username for the superuser'
        )
        parser.add_argument(
            '--password', 
            default='admin123', 
            help='Password for the superuser'
        )
        parser.add_argument(
            '--email', 
            default='admin@example.com', 
            help='Email for the superuser'
        )

    def handle(self, *args, **options):
        # Get database connection parameters from settings
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']
        
        self.stdout.write(self.style.SUCCESS(f'Resetting database: {db_name}'))
        
        # Drop and recreate database
        with connection.cursor() as cursor:
            # Disconnect all users
            cursor.execute(
                "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                "FROM pg_stat_activity "
                "WHERE pg_stat_activity.datname = %s "
                "AND pid <> pg_backend_pid();", 
                [db_name]
            )
            
            # Close connection to the database
            connection.close()
            
            # Connect to postgres database to drop and recreate target database
            os_command = f'PGPASSWORD="{db_password}" psql -h {db_host} -p {db_port} -U {db_user} -d postgres -c "DROP DATABASE IF EXISTS {db_name};"'
            os.system(os_command)
            
            os_command = f'PGPASSWORD="{db_password}" psql -h {db_host} -p {db_port} -U {db_user} -d postgres -c "CREATE DATABASE {db_name} WITH OWNER = {db_user};"'
            os.system(os_command)
            
        # Run migrations
        self.stdout.write(self.style.SUCCESS('Running migrations...'))
        call_command('migrate')
        
        # Create superuser
        username = options['username']
        password = options['password']
        email = options['email']
        
        self.stdout.write(self.style.SUCCESS(f'Creating superuser: {username}'))
        
        from django.contrib.auth.models import User
        User.objects.create_superuser(username=username, email=email, password=password)
        
        self.stdout.write(self.style.SUCCESS('Database reset completed!'))
        self.stdout.write(self.style.SUCCESS(f'Superuser created with username: {username} and password: {password}')) 
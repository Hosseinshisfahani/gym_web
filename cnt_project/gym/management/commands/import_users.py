import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gym.models import UserProfile

class Command(BaseCommand):
    help = 'Import users from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        try:
            # Read the Excel file
            self.stdout.write('Reading Excel file...')
            df = pd.read_excel(file_path)
            
            # Print column names for debugging
            self.stdout.write(f'Found columns: {", ".join(df.columns)}')
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row['کدملی']):
                        continue
                        
                    # Get melli code
                    melli_code = str(row['کدملی']).strip()
                    
                    # Check if user profile already exists
                    if UserProfile.objects.filter(melli_code=melli_code).exists():
                        self.stdout.write(self.style.WARNING(f'User with melli code {melli_code} already exists'))
                        continue
                    
                    # Get full name
                    full_name = str(row['نام و نام خانوادگی']).strip()
                    name_parts = full_name.split()
                    first_name = name_parts[0] if name_parts else ''
                    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    
                    # Create username from melli code
                    username = f"user_{melli_code}"
                    
                    # Create or update user
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': f"{username}@example.com",
                        }
                    )
                    
                    if created:
                        # Set a default password
                        user.set_password('default_password123')
                        user.save()
                        
                        # Create user profile
                        UserProfile.objects.create(
                            user=user,
                            melli_code=melli_code,
                            phone_number='',  # You can add phone number if available
                            full_name=full_name,
                        )
                        
                        self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user.username}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'User already exists: {user.username}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing row {index}: {str(e)}'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading Excel file: {str(e)}')) 
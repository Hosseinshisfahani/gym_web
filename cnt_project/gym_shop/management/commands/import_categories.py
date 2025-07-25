import os
import json
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from gym_shop.models import Category
from datetime import datetime


class Command(BaseCommand):
    help = 'Import shop categories data and images from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to the categories export JSON file'
        )
        parser.add_argument(
            '--images-dir',
            type=str,
            help='Directory containing category images (default: images/ in same directory as JSON)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing categories before import'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing categories instead of creating new ones'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        images_dir = options['images_dir']
        clear_existing = options['clear_existing']
        update_existing = options['update_existing']
        
        # Check if JSON file exists
        if not os.path.exists(json_file):
            self.stdout.write(
                self.style.ERROR(f'JSON file not found: {json_file}')
            )
            return
        
        # Determine images directory
        if not images_dir:
            json_dir = os.path.dirname(json_file)
            images_dir = os.path.join(json_dir, 'images')
        
        # Load JSON data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading JSON file: {e}')
            )
            return
        
        # Extract data
        metadata = export_data.get('metadata', {})
        categories_data = export_data.get('categories', [])
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {len(categories_data)} categories in export file')
        )
        
        # Clear existing categories if requested
        if clear_existing:
            Category.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Cleared all existing categories')
            )
        
        # Import categories
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        
        for category_data in categories_data:
            try:
                # Check if category exists
                existing_category = None
                if update_existing:
                    existing_category = Category.objects.filter(slug=category_data['slug']).first()
                
                if existing_category:
                    # Update existing category
                    for field, value in category_data.items():
                        if field not in ['id', 'image_filename'] and hasattr(existing_category, field):
                            setattr(existing_category, field, value)
                    
                    category = existing_category
                    updated_count += 1
                else:
                    # Create new category
                    category = Category(
                        name=category_data['name'],
                        name_en=category_data['name_en'],
                        slug=category_data['slug'],
                        description=category_data['description'],
                        is_active=category_data['is_active']
                    )
                    imported_count += 1
                
                # Handle image
                if category_data.get('image_filename'):
                    image_path = os.path.join(images_dir, category_data['image_filename'])
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as img_file:
                            category.image.save(
                                category_data['image_filename'],
                                File(img_file),
                                save=False
                            )
                        self.stdout.write(
                            f'  ✓ Added image for category: {category.name}'
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Image not found: {image_path}')
                        )
                
                category.save()
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error importing category {category_data.get("name", "Unknown")}: {e}')
                )
                skipped_count += 1
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed successfully!'
            )
        )
        self.stdout.write(f'  • Imported: {imported_count} categories')
        self.stdout.write(f'  • Updated: {updated_count} categories')
        self.stdout.write(f'  • Skipped: {skipped_count} categories')
        
        # Show metadata
        if metadata:
            self.stdout.write(f'\nExport Information:')
            self.stdout.write(f'  • Export Date: {metadata.get("export_date", "Unknown")}')
            self.stdout.write(f'  • Total Categories: {metadata.get("total_categories", "Unknown")}')
            self.stdout.write(f'  • Active Categories: {metadata.get("active_categories", "Unknown")}')
            self.stdout.write(f'  • Images Included: {metadata.get("include_images", "Unknown")}') 
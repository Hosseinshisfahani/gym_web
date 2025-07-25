import os
import json
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from gym_shop.models import Category
from datetime import datetime


class Command(BaseCommand):
    help = 'Export shop categories data and images to a JSON file and images folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='category_export',
            help='Output directory for exported data (default: category_export)'
        )
        parser.add_argument(
            '--include-images',
            action='store_true',
            help='Include category images in the export'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        include_images = options['include_images']
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create images subdirectory if needed
        images_dir = os.path.join(output_dir, 'images')
        if include_images and not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # Get all categories
        categories = Category.objects.all()
        
        # Prepare data for export
        categories_data = []
        
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'name_en': category.name_en,
                'slug': category.slug,
                'description': category.description,
                'is_active': category.is_active,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None,
            }
            
            # Handle image
            if include_images and category.image:
                image_path = category.image.path
                if os.path.exists(image_path):
                    # Copy image to export directory
                    image_filename = os.path.basename(image_path)
                    new_image_path = os.path.join(images_dir, image_filename)
                    shutil.copy2(image_path, new_image_path)
                    category_data['image_filename'] = image_filename
                else:
                    category_data['image_filename'] = None
            else:
                category_data['image_filename'] = None
            
            categories_data.append(category_data)
        
        # Create metadata
        metadata = {
            'export_date': datetime.now().isoformat(),
            'total_categories': len(categories_data),
            'active_categories': len([c for c in categories_data if c['is_active']]),
            'include_images': include_images,
            'version': '1.0'
        }
        
        # Export data
        export_data = {
            'metadata': metadata,
            'categories': categories_data
        }
        
        # Save to JSON file
        json_file_path = os.path.join(output_dir, 'categories_export.json')
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # Create README file
        readme_content = f"""# Shop Categories Export

This directory contains exported shop categories data from the gym web application.

## Files:
- `categories_export.json` - Categories data in JSON format
- `images/` - Category images (if included in export)

## Export Information:
- Export Date: {metadata['export_date']}
- Total Categories: {metadata['total_categories']}
- Active Categories: {metadata['active_categories']}
- Images Included: {metadata['include_images']}

## Import Instructions:
1. Copy the `categories_export.json` file to your Django project
2. Copy the `images/` folder to your media directory
3. Run: `python manage.py import_categories categories_export.json`

## Data Structure:
Each category contains:
- id: Database ID
- name: Persian name
- name_en: English name
- slug: URL slug
- description: Category description
- is_active: Active status
- created_at: Creation date
- updated_at: Last update date
- image_filename: Image file name (if exists)
"""
        
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully exported {len(categories_data)} categories to {output_dir}/'
            )
        )
        
        if include_images:
            image_count = len([c for c in categories_data if c['image_filename']])
            self.stdout.write(
                self.style.SUCCESS(f'Exported {image_count} category images')
            ) 
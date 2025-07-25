# Shop Categories Export

This directory contains exported shop categories data from the gym web application.

## Files:
- `categories_export.json` - Categories data in JSON format
- `images/` - Category images (if included in export)

## Export Information:
- Export Date: 2025-07-26T03:06:45.763279
- Total Categories: 5
- Active Categories: 5
- Images Included: True

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

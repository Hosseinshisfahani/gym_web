# Shop Categories Transfer Guide

This guide explains how to transfer your shop categories data (including images) to GitHub and share it with others.

## 🎯 Overview

The shop categories transfer system allows you to:
- Export categories data and images to a portable format
- Share the data via GitHub
- Import the data into other Django projects
- Maintain data integrity and relationships

## 📁 File Structure

After export, you'll have:
```
category_export/
├── categories_export.json    # Categories data
├── images/                   # Category images
│   ├── category1.jpg
│   ├── category2.png
│   └── ...
└── README.md                 # Export documentation
```

## 🚀 Step-by-Step Process

### 1. Export Categories Data

Navigate to your Django project directory and run:

```bash
cd cnt_project
python manage.py export_categories --include-images --output-dir category_export
```

**Options:**
- `--include-images`: Include category images in the export
- `--output-dir`: Specify output directory (default: `category_export`)

### 2. Review Exported Data

Check the exported files:
```bash
ls -la category_export/
cat category_export/README.md
```

### 3. Add to Git Repository

```bash
# Add the export directory to your repository
git add category_export/
git commit -m "Add shop categories export data

- Export categories data and images
- Include metadata and documentation
- Ready for sharing and import"
git push origin main
```

### 4. Share on GitHub

The exported data is now available in your GitHub repository at:
```
https://github.com/yourusername/gym_web/tree/main/category_export
```

## 📥 Importing Categories Data

### For Other Developers

To import the categories data into another Django project:

1. **Download the export data:**
   ```bash
   # Clone or download the repository
   git clone https://github.com/yourusername/gym_web.git
   cd gym_web/category_export
   ```

2. **Copy to your Django project:**
   ```bash
   # Copy the JSON file and images to your project
   cp categories_export.json /path/to/your/django/project/
   cp -r images/ /path/to/your/django/project/
   ```

3. **Import the data:**
   ```bash
   cd /path/to/your/django/project
   python manage.py import_categories categories_export.json
   ```

### Import Options

```bash
# Basic import
python manage.py import_categories categories_export.json

# Import with custom images directory
python manage.py import_categories categories_export.json --images-dir /path/to/images

# Clear existing categories before import
python manage.py import_categories categories_export.json --clear-existing

# Update existing categories instead of creating new ones
python manage.py import_categories categories_export.json --update-existing
```

## 📊 Data Structure

### Categories JSON Format

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00",
    "total_categories": 5,
    "active_categories": 4,
    "include_images": true,
    "version": "1.0"
  },
  "categories": [
    {
      "id": 1,
      "name": "لباس ورزشی",
      "name_en": "Sportswear",
      "slug": "sportswear",
      "description": "لباس‌های ورزشی با کیفیت بالا",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:30:00",
      "image_filename": "sportswear.jpg"
    }
  ]
}
```

### Category Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Database ID |
| `name` | String | Persian name |
| `name_en` | String | English name |
| `slug` | String | URL slug |
| `description` | Text | Category description |
| `is_active` | Boolean | Active status |
| `created_at` | DateTime | Creation date |
| `updated_at` | DateTime | Last update date |
| `image_filename` | String | Image file name |

## 🔧 Advanced Usage

### Custom Export Directory

```bash
python manage.py export_categories --output-dir my_custom_export --include-images
```

### Export Without Images

```bash
python manage.py export_categories --output-dir category_export
```

### Batch Import Multiple Exports

```bash
# Import multiple export files
for file in exports/*.json; do
    python manage.py import_categories "$file" --update-existing
done
```

## 🛠️ Troubleshooting

### Common Issues

1. **Image files not found during import:**
   - Ensure the `images/` directory is in the same location as the JSON file
   - Check file permissions
   - Verify image file names match the JSON data

2. **Duplicate slug errors:**
   - Use `--update-existing` to update existing categories
   - Use `--clear-existing` to remove all existing categories first

3. **Encoding issues:**
   - Ensure JSON files are saved with UTF-8 encoding
   - Check Django settings for proper Unicode support

### Error Messages

- `JSON file not found`: Check the file path
- `Error reading JSON file`: Verify JSON syntax
- `Image not found`: Check image file paths and permissions

## 📝 Best Practices

1. **Regular Exports:** Export categories data regularly to maintain backups
2. **Version Control:** Include export data in your Git repository
3. **Documentation:** Always include README files with export information
4. **Testing:** Test imports in a development environment first
5. **Backup:** Keep backups of your original database

## 🔄 Automation

### Automated Export Script

Create a script to automate regular exports:

```bash
#!/bin/bash
# auto_export_categories.sh

DATE=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="category_exports/export_$DATE"

cd /path/to/your/django/project
python manage.py export_categories --include-images --output-dir "$EXPORT_DIR"

# Add to git
git add "$EXPORT_DIR"
git commit -m "Auto export categories - $DATE"
git push origin main
```

### Cron Job

Add to crontab for daily exports:
```bash
0 2 * * * /path/to/auto_export_categories.sh
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django documentation
3. Check the export/import command help: `python manage.py export_categories --help`

---

**Note:** This system is designed for Django projects with the `gym_shop` app. Ensure your target project has the same model structure for successful imports. 
from django.core.management.base import BaseCommand
from gym.models import TuitionCategory


class Command(BaseCommand):
    help = 'Create sample tuition categories for testing'

    def handle(self, *args, **options):
        # Create sample tuition categories
        categories_data = [
            {
                'name': 'ماهانه',
                'description': 'شهریه ماهانه باشگاه',
                'amount': 500000,
                'duration_months': 1,
                'is_active': True,
            },
            {
                'name': 'فصلی',
                'description': 'شهریه فصلی باشگاه (۳ ماه)',
                'amount': 1400000,
                'duration_months': 3,
                'is_active': True,
            },
            {
                'name': 'شش ماهه',
                'description': 'شهریه شش ماهه باشگاه',
                'amount': 2600000,
                'duration_months': 6,
                'is_active': True,
            },
            {
                'name': 'سالانه',
                'description': 'شهریه سالانه باشگاه (۱۲ ماه)',
                'amount': 4800000,
                'duration_months': 12,
                'is_active': True,
            },
        ]

        created_count = 0
        for category_data in categories_data:
            category, created = TuitionCategory.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created tuition category: {category.name} - {category.amount:,} تومان'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Tuition category already exists: {category.name}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} new tuition categories'
            )
        )

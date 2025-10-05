from django.core.management.base import BaseCommand
from gym_shop.models import Product, ExchangeRate


class Command(BaseCommand):
    help = 'Update dollar prices for all products based on current exchange rate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        try:
            exchange_rate = ExchangeRate.objects.filter(is_active=True).latest('created_at')
            self.stdout.write(f'Using exchange rate: 1 USD = {exchange_rate.rate} Toman')
        except ExchangeRate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('No active exchange rate found. Please set one first.')
            )
            return

        products = Product.objects.all()
        updated_count = 0

        for product in products:
            # Calculate dollar price from Toman price
            dollar_price = round(product.price / exchange_rate.rate, 2)
            discount_dollar_price = None
            
            if product.discount_price:
                discount_dollar_price = round(product.discount_price / exchange_rate.rate, 2)

            if not dry_run:
                product.dollar_price = dollar_price
                if discount_dollar_price:
                    product.discount_dollar_price = discount_dollar_price
                product.save()
                updated_count += 1
            else:
                self.stdout.write(
                    f'Would update {product.name}: {product.price} Toman -> ${dollar_price} USD'
                )
                if discount_dollar_price:
                    self.stdout.write(
                        f'  Discount: {product.discount_price} Toman -> ${discount_dollar_price} USD'
                    )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated dollar prices for {updated_count} products'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Dry run completed. Would update {len(products)} products. '
                    'Run without --dry-run to apply changes.'
                )
            )

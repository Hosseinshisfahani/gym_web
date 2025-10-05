from django.core.management.base import BaseCommand
from gym_shop.models import ExchangeRate


class Command(BaseCommand):
    help = 'Set the initial USD to Toman exchange rate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rate',
            type=float,
            default=4205.0,
            help='Exchange rate (1 USD = X Toman). Default: 4205.0'
        )

    def handle(self, *args, **options):
        rate = options['rate']
        
        # Deactivate all existing rates
        ExchangeRate.objects.filter(is_active=True).update(is_active=False)
        
        # Create new active rate
        exchange_rate = ExchangeRate.objects.create(
            rate=rate,
            is_active=True,
            source='Management Command'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set exchange rate: 1 USD = {rate} Toman'
            )
        )

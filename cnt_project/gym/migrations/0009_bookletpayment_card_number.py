# Generated by Django 5.0.2 on 2025-05-11 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0008_payment_card_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookletpayment',
            name='card_number',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='شماره کارت'),
        ),
    ]

# Generated by Django 5.2 on 2025-05-06 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0003_planrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'در انتظار بررسی'), ('approved', 'تایید شده'), ('rejected', 'رد شده'), ('completed', 'تکمیل شده')], default='pending', max_length=10, verbose_name='وضعیت'),
        ),
    ]

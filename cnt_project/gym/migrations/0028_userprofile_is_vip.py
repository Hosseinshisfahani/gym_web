# Generated by Django 4.2.16 on 2025-07-12 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0027_add_goal_directions'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_vip',
            field=models.BooleanField(default=False, verbose_name='کاربر VIP'),
        ),
    ]

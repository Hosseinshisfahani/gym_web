# Generated by Django 4.2.16 on 2025-07-14 21:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0031_add_workout_plan_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workoutplan',
            name='title',
        ),
    ]

# Generated by Django 5.2.4 on 2025-07-06 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_event_options_remove_event_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('Physical', 'Physical'), ('Online', 'Online'), ('Hybrid', 'Hybrid')], default='Physical', help_text='The format of the event.', max_length=10),
        ),
        migrations.AddField(
            model_name='event',
            name='online_link',
            field=models.URLField(blank=True, help_text='The meeting/stream link for online or hybrid events.', max_length=255),
        ),
        migrations.AddField(
            model_name='event',
            name='physical_location',
            field=models.CharField(blank=True, help_text='The address or venue for physical or hybrid events.', max_length=255),
        ),
    ]

# Generated by Django 4.1.13 on 2024-04-10 04:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('downloader', '0002_alter_playersnapshot_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='lastpolled',
            field=models.IntegerField(null=True),
        ),
    ]

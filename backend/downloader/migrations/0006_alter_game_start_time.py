# Generated by Django 4.1.13 on 2024-04-10 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('downloader', '0005_alter_game_diplomacy_type_alter_game_map_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='start_time',
            field=models.IntegerField(),
        ),
    ]

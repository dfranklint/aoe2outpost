# Generated by Django 4.1.13 on 2024-04-09 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('game_id', models.IntegerField(primary_key=True, serialize=False)),
                ('diplomacy_type', models.SmallIntegerField()),
                ('start_time', models.DateTimeField()),
                ('map_id', models.SmallIntegerField()),
                ('winner', models.SmallIntegerField()),
                ('downloaded', models.CharField(choices=[(0, 'Pending'), (1, 'Completed'), (2, 'Failed')], max_length=12)),
            ],
        ),
        migrations.CreateModel(
            name='GameMetadata',
            fields=[
                ('game_id', models.IntegerField(primary_key=True, serialize=False)),
                ('map_seed', models.BigIntegerField()),
                ('game_version', models.TextField()),
                ('average_rating', models.SmallIntegerField()),
                ('metadata_version', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Map',
            fields=[
                ('map_id', models.SmallIntegerField(primary_key=True, serialize=False)),
                ('map_name', models.TextField()),
                ('dimension', models.SmallIntegerField()),
                ('official', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('profile_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('alias', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PlayerSnapshot',
            fields=[
                ('id', models.IntegerField(auto_created=True, primary_key=True, serialize=False)),
                ('profile_id', models.IntegerField()),
                ('diplomacy_type', models.SmallIntegerField()),
                ('wins', models.IntegerField(null=True)),
                ('losses', models.IntegerField(null=True)),
                ('streak', models.SmallIntegerField(null=True)),
                ('drops', models.SmallIntegerField(null=True)),
                ('rank', models.IntegerField(null=True)),
                ('rating', models.SmallIntegerField(null=True)),
                ('lastmatchdate', models.IntegerField(null=True)),
            ],
            options={
                'unique_together': {('profile_id', 'diplomacy_type', 'lastmatchdate')},
            },
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_id', models.IntegerField()),
                ('profile_id', models.IntegerField()),
                ('civ_id', models.SmallIntegerField()),
                ('player_position', models.SmallIntegerField()),
                ('rating', models.SmallIntegerField(null=True)),
            ],
            options={
                'unique_together': {('game_id', 'profile_id')},
            },
        ),
    ]

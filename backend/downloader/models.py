from django.db import models

class Player(models.Model):
    profile_id = models.IntegerField(primary_key=True)
    name = models.TextField()
    alias = models.TextField()
    lastpolled = models.IntegerField(null=True)

class PlayerSnapshot(models.Model):
    profile_id = models.IntegerField()
    diplomacy_type = models.SmallIntegerField()
    wins = models.IntegerField(null=True)
    losses = models.IntegerField(null=True)
    streak = models.SmallIntegerField(null=True)
    drops = models.SmallIntegerField(null=True)
    rank = models.IntegerField(null=True)
    rating = models.SmallIntegerField(null=True)
    lastmatchdate = models.IntegerField(null=True)

    class Meta:
        unique_together = ['profile_id', 'diplomacy_type', 'lastmatchdate']

class Game(models.Model):
    game_id = models.IntegerField(primary_key=True)
    diplomacy_type = models.SmallIntegerField(null=True)
    start_time = models.IntegerField(null=True)
    map_id = models.SmallIntegerField(null=True)
    creator_profile_id = models.IntegerField(null=True)
    downloaded_as_int = [
        (0, 'Pending'),
        (1, 'Completed'),
        (2, '404 Not Found'),
        (3, '429 Rate Limited'),
        (4, '403 Refused Request'),
        (5, 'other error')
    ]
    downloaded = models.CharField(max_length=12, choices=downloaded_as_int)

class GamePlayer(models.Model):
    game_id = models.IntegerField()
    profile_id = models.IntegerField()
    civ_id = models.SmallIntegerField(null=True)
    player_position = models.SmallIntegerField(null=True)
    rating = models.SmallIntegerField(null=True)

    class Meta:
        unique_together = ['game_id', 'profile_id']

class GamePlayerMetadata(models.Model):
    game_id = models.IntegerField()
    profile_id = models.IntegerField()
    loom_timing = models.DurationField(null=True)
    wheelbarrow_timing = models.DurationField(null=True)
    data_version = models.SmallIntegerField(null=True)

    class Meta:
        unique_together = ['game_id', 'profile_id']

class GameMetadata(models.Model):
    game_id = models.IntegerField(primary_key=True)
    map_seed = models.BigIntegerField()
    game_version = models.TextField()
    average_rating = models.SmallIntegerField()
    data_version = models.SmallIntegerField(null=True)

class Map(models.Model):
    map_id = models.SmallIntegerField(primary_key=True)
    map_name = models.TextField()
    dimension = models.SmallIntegerField()
    official = models.BooleanField()

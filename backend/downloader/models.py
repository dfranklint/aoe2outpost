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
        (5, 'other error'),
        (6, 'Runtime error')
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
    data_version = models.SmallIntegerField(null=True)
    rating = models.SmallIntegerField(null=True)
    winner = models.BooleanField(null=True)
    prefer_random = models.BooleanField(null=True)
    civilization = models.TextField(null=True)
    eapm = models.SmallIntegerField(null=True)

    loom_timing = models.DurationField(null=True)
    wheelbarrow_timing = models.DurationField(null=True)
    hand_cart_timing = models.DurationField(null=True)
    double_bit_axe_timing = models.DurationField(null=True)
    bow_saw_timing = models.DurationField(null=True)
    two_man_saw_timing = models.DurationField(null=True)
    gillnets_timing = models.DurationField(null=True)
    feudal_age_timing = models.DurationField(null=True)
    castle_age_timing = models.DurationField(null=True)
    imperial_age_timing = models.DurationField(null=True)
    gold_mining_timing = models.DurationField(null=True)
    gold_shaft_mining_timing = models.DurationField(null=True)
    horse_collar_timing = models.DurationField(null=True)
    heavy_plow_timing = models.DurationField(null=True)
    crop_rotation_timing = models.DurationField(null=True)
    stone_mining_timing = models.DurationField(null=True)
    stone_shaft_mining_timing = models.DurationField(null=True)
    town_watch_timing = models.DurationField(null=True)
    herbal_medicine_timing = models.DurationField(null=True)

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

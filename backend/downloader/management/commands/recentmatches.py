from django.core.management.base import BaseCommand
from downloader.models import Player, Game, GamePlayer, GamePlayerMetadata
from itertools import islice
import requests
import json
import os
import datetime
import time

class Command(BaseCommand):
    help = 'Fetches recent matches for players within a specified rank range'

    def add_arguments(self, parser):
        parser.add_argument('batch_size', type=int, help='batch size of players for each recentmatches api request')

    def fetch_recent_matches(self, profile_ids):
        profile_ids_str = ', '.join(str(id) for id in profile_ids)
        url = f"https://aoe-api.reliclink.com/community/leaderboard/getRecentMatchHistory?title=age2&profile_ids=[{profile_ids_str}]"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch recent matches for {profile_ids_str}: {response.status_code}")
            return None

    def extract_game_data(self, response):
        matchHistoryStats = response.get("matchHistoryStats", [])
        downloaded = 0
        for match in matchHistoryStats:
            if match.get("description") != "AUTOMATCH":
                print(match.get("description"))
                print("not an automatch")
                continue

            if match.get("maxplayers") != 2:
                print("not 1v1")
                continue

            game_id = match.get("id")
            diplomacy_type = 1 # 1 for 1v1 for now
            start_time = match.get("startgametime")
            creator_profile_id = match.get("creator_profile_id")
            #TODO map_id = match.get("") # rethink model?

            # Create or update Player instance
            game, game_created = Game.objects.get_or_create(game_id=game_id)
            if game_created:
                print("New game created.")
                game.game_id = game_id
                game.diplomacy_type = diplomacy_type
                game.start_time = start_time
                game.creator_profile_id = creator_profile_id
                game.downloaded = downloaded
                game.save()
            else:
                print("Game already exists.")
                continue

            game_players = match.get("matchhistorymember")

            for player in game_players:
                profile_id = player.get("profile_id")
                game_player, game_player_created = GamePlayer.objects.get_or_create(game_id=game_id, profile_id=profile_id)
                if game_player_created:
                    game_player_meta, game_player_meta_created = GamePlayerMetadata.get_or_create(game_id=game_id, profile_id=profile_id)
                    print("New game player created.")
                    game_player.game_id = game_id
                    game_player.profile_id = profile_id
                    game_player.civ_id = player.get("race_id")
                    game_player.rating = player.get("oldrating")
                    game_player.save()
                    game_player_meta.save()
                else:
                    print("Game player already exists.")
        return



    def handle(self, *args, **options):
        batch_size = options['batch_size']
        players_iterator = Player.objects.all().iterator()
        batch_num = 0

        while True:
            batch = list(islice(players_iterator, batch_size))
            print(batch_num)
            if not batch:
                break
            profile_ids = [player.profile_id for player in batch]
            print(f"players: {profile_ids}\n")
            response = self.fetch_recent_matches(profile_ids)
            current_epoch_time = int(time.time())
            self.extract_game_data(response)
            for player in batch:
                player.lastpolled = current_epoch_time
                player.save(update_fields=['lastpolled'])
            batch_num += 1
        return

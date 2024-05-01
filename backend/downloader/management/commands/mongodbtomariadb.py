from pymongo import MongoClient
from django.core.management.base import BaseCommand
from ...utils import get_db_handle
from downloader.models import Game, GamePlayer, GamePlayerMetadata
from django.db.models import Q
from itertools import islice
from datetime import timedelta
import os


class Command(BaseCommand):
    help = 'Extract from MongoDB the research timings of every tech and place into MariaDB'

    def add_arguments(self, parser):
        parser.add_argument('batch_size', type=int, help='batch size of game_ids pulled from MariaDB per MongoDB operation')

    def timestamp_str_to_timedelta(self, timestamp_str):

        components = timestamp_str.split(':')
        hours = int(components[0])
        minutes = int(components[1])

        # Split the seconds part to check if there are milliseconds
        seconds_components = components[2].split('.')
        seconds = int(seconds_components[0])

        # Set microseconds to 0 if there are no milliseconds
        microseconds = int(seconds_components[1]) if len(seconds_components) > 1 else 0

        duration = timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)

        return duration


    def upload_from_player(self, db_handle, client, game_ids):
        print("running upload_from_player")
        game_recordings_collection = db_handle.game_recordings
        # Aggregation pipeline to filter documents
        pipeline = [
            {"$match": {"_id": {"$in": game_ids}}},  # Assuming you have game_ids defined
            {"$unwind": "$data.players"},
            {"$project": {
                "winner": "$data.players.winner",
                "eapm": "$data.players.eapm",
                "prefer_random": "data.players.prefer_random",
                "civilization": "data.players.civilization",
                "profile_id": "$data.players.profile_id"
            }}
        ]

        # Execute the aggregation pipeline
        cursor = game_recordings_collection.aggregate(pipeline)

        # Iterate over actions and print/upload extracted timestamps
        for document in cursor:
            print(f"processing document with id: {document.get('_id')}")
            gameplayermeta, gameplayermeta_created = GamePlayerMetadata.objects.get_or_create(
                    game_id=document.get('_id'),
                    profile_id=document.get('profile_id'),
                )
            setattr(gameplayermeta, "civilization", document.get('civilization'))
            setattr(gameplayermeta, "eapm", document.get('eapm'))
            setattr(gameplayermeta, "prefer_random", document.get('prefer_random').lower() == "true") # convert string to boolean
            setattr(gameplayermeta, "winner", document.get('winner')) # TODO Why doesnt this one have to get converted to boolean?
            gameplayermeta.save()

        return





    def upload_timings(self, db_handle, client, game_ids): # fetches research timings from MongoDB and updates MariaDB
#        print("upload function called\n")
        game_recordings_collection = db_handle.game_recordings

        # List of technology names (as found in the json) to include in MariaDB
        technology_names = [
            "Loom",
            "Wheelbarrow",
            "Hand Cart",
            "Double-Bit Axe",
            "Bow Saw",
            "Two-Man Saw",
            "Gillnets",
            "Feudal Age",
            "Castle Age",
            "Imperial Age",
            "Gold Mining",
            "Gold Shaft Mining",
            "Horse Collar",
            "Heavy Plow",
            "Crop Rotation",
            "Stone Mining",
            "Stone Shaft Mining",
            "Town Watch",
            "Herbal Medicine",
        ]

        # Aggregation pipeline to filter documents based on technology names and game_ids and extract timestamp
        pipeline = [
            {"$match": {"_id": {"$in": game_ids}}},
            {"$match": {"data.actions.type": "RESEARCH"}},
            {"$unwind": "$data.actions"},
            {"$match": {"data.actions.payload.technology": {"$in": technology_names}}},
            {"$project": {
                "timestamp": "$data.actions.timestamp",
                "technology": "$data.actions.payload.technology",
                "player": "$data.actions.player",
                "profile_ids": "$data.players.profile_id", # profile_ids is an array where data.players.number is in index-1
            }}
        ]


        # Execute the aggregation pipeline
        cursor = game_recordings_collection.aggregate(pipeline)

        # Iterate over actions and print/upload extracted timestamps
        for document in cursor:
#            print(f"processing document with id: {document.get('_id')}")
            timestamp_str = document.get('timestamp')
            timestamp_td = self.timestamp_str_to_timedelta(timestamp_str)
            technology = document.get('technology')
            player = document.get('player')
            profile_ids = document.get('profile_ids')
            profile_id = profile_ids[player-1]
            game_id = document.get('_id')
            if timestamp_str:
#                print(f"game_id: {game_id}, Player: {player}, profile_ids: {profile_ids}, profile_id: {profile_id}, Technology: {technology}, Timestamp str: {timestamp_str}, Timestamp td: {timestamp_td}\n")
                timing_field = technology.replace(" ", "_").replace("-", "_").lower() + "_timing"
                # Get or create a GamePlayerMetadata entry for the combination of profile_id and game_id
                gameplayermeta, gameplayermeta_created = GamePlayerMetadata.objects.get_or_create(
                    game_id=game_id,
                    profile_id=profile_id,
                )
                setattr(gameplayermeta, timing_field, timestamp_td)
                gameplayermeta.save()

        return

    def create_new_gameplayermetadatas(self): # Populate empty GamePlayerMetadata entries for newly downloaded games
        # Get all downloaded games
        downloaded_games = Game.objects.filter(downloaded=1)
        gameplayermetadatas_checked = 0

        # Iterate over downloaded games
        for game in downloaded_games:
            # Get all players of the game
            players = GamePlayer.objects.filter(game_id=game.game_id)
            for player in players:
                # Get or create metadata
                GamePlayerMetadata.objects.get_or_create(
                    game_id=game.game_id, # This could be player.game_id, too
                    profile_id=player.profile_id,
                )
                gameplayermetadatas_checked += 1
                print (f"Checked {gameplayermetadatas_checked} gameplayermetadatas\n")
        return

    def copy_from_gameplayer_to_gameplayermetadata(self):
        # Get all downloaded games
        downloaded_games = Game.objects.filter(downloaded=1)
        gameplayermetadatas_appended = 0

        # Iterate over downloaded games
        for game in downloaded_games:
            # Get all players of the game
            players = GamePlayer.objects.filter(game_id=game.game_id)
            for player in players:
                # Get or create metadata
                metadata, created = GamePlayerMetadata.objects.get_or_create(
                    game_id=game.game_id,
                    profile_id=player.profile_id,
                )
                if created or metadata.rating is None:
                    # If created or rating is None, set the rating
                    metadata.rating = player.rating
                    metadata.save()
                    gameplayermetadatas_appended += 1
                    print(f"Appended {gameplayermetadatas_appended} gameplayermetadatas\n")
        return


    def handle(self, *args, **options):

        new_data_version = 5

        # establish MongoDB connection
        db_name = 'aoe2db'
        host = 'localhost'
        port = 27017
        username = os.environ.get('MONGODB_USERNAME')
        password = os.environ.get('MONGODB_PASSWORD')
        db_handle, client = get_db_handle(db_name, host, port, username, password)

#        self.create_new_gameplayermetadatas()
#        self.copy_from_gameplayer_to_gameplayermetadata()

        batch_size = options['batch_size']

        # Fetch game_ids in GamePlayerMetadata with outdated data_version
        queryset = (
            GamePlayerMetadata.objects
            .filter(Q(data_version__lt=new_data_version) | Q(data_version__isnull=True))
            .order_by('id')
            .values_list('game_id', flat=True)
        )

        game_ids_iterator = iter(queryset)
        batch_num = 0

        while True:
            print(f"batch  {batch_num}")
            batch = list(islice(game_ids_iterator, batch_size))
            if not batch:
                print("no more batches\n")
                break
            self.upload_timings(db_handle, client, batch)
            self.upload_from_player(db_handle, client, batch)
            GamePlayerMetadata.objects.filter(game_id__in=batch).update(data_version=new_data_version) # update data_version in MariaDB
            batch_num += 1

        return


from pymongo import MongoClient
from django.core.management.base import BaseCommand
from ...utils import get_db_handle
from downloader.models import Game, GamePlayerMetadata
from django.db.models import Q
from itertools import islice
from datetime import timedelta
import os


class Command(BaseCommand):
    help = 'Extract from MongoDB the research timings of every tech and place into MariaDB'

    def add_arguments(self, parser):
        parser.add_argument('batch_size', type=int, help='batch size of players for each recentmatches api request')

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

    def upload_timings(self, db_handle, client, game_ids): # fetches research timings from MongoDB and updates MariaDB
#        print("upload function called\n")
        game_recordings_collection = db_handle.game_recordings

        # List of technology names to include in MariaDB
        technology_names = [
            "Wheelbarrow",
            "Loom",
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
                timing_field = technology.lower() + "_timing"

                # Get or create a GamePlayerMetadata entry for the combination of profile_id and game_id
                gameplayermeta, gameplayermeta_created = GamePlayerMetadata.objects.get_or_create(
                    game_id=game_id,
                    profile_id=profile_id,
                )
                setattr(gameplayermeta, timing_field, timestamp_td)
                gameplayermeta.save()

    def handle(self, *args, **options):

        new_data_version = 1

        # establish MongoDB connection
        db_name = 'aoe2db'
        host = 'localhost'
        port = 27017
        username = os.environ.get('MONGODB_USERNAME')
        password = os.environ.get('MONGODB_PASSWORD')
        db_handle, client = get_db_handle(db_name, host, port, username, password)

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
            GamePlayerMetadata.objects.filter(game_id__in=batch).update(data_version=new_data_version) # update data_version in MariaDB
            batch_num += 1


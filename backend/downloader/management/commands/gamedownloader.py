from django.core.management.base import BaseCommand
from ...utils import get_db_handle
from itertools import islice
from downloader.models import Game
from mgz.model import parse_match, serialize
from pymongo import MongoClient
import requests
import json
import os
import datetime
import time
import io
import zipfile

class Command(BaseCommand):
    help = 'Download game files from API and update successful and unsuccessful downloads'

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

    def add_arguments(self, parser):
        parser.add_argument('batch_size', type=int, help='batch size of players for each recentmatches api request')
        parser.add_argument('oldest_age', type=int, help='the oldest age of game in hours to attempt to download')


    def download_game_file(self, game_id, creator_id):
        url = f"https://aoe.ms/replay/?gameId={game_id}&profileId={creator_id}"
        headers = {'User-Agent': self.USER_AGENT}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            self.stdout.write(f"Failed to download game file for game_id={game_id}. Status code: {response.status_code}")
            self.stdout.write(f"Response content: {response.content}")
            return None, response.status_code
        return response.content, response.status_code

    def replay_parser(self, game_recording):
        output_directory = '/home/chad/aoe2outpost/parsedfiles'
        match = parse_match(game_recording)
        serialized_data = serialize(match)
        self.stdout.write(f"Processed.")
        del serialized_data["gaia"]
        del serialized_data["map"]
        del serialized_data["inputs"]
        return serialized_data

    def decompress(self, game_file_compressed):
        game_file_compressed_io = io.BytesIO(game_file_compressed)

        with zipfile.ZipFile(game_file_compressed_io, 'r') as zip_ref:
            decompressed = zip_ref.open(zip_ref.namelist()[0])
        return decompressed

    def insert_into_mongodb(self, game_id, json_dump, db_handle):
        existing_document = db_handle.game_recordings.find_one({'_id': game_id})
        if existing_document is not None:
            print(f"Entry already exists in mongodb. Skipping.")
            return 0
        # Create the document to insert
        document = {
            '_id': game_id,
            'data': json_dump
        }
        # Insert the document into the collection
        db_handle.game_recordings.insert_one(document)
        return 1

    def handle(self, *args, **options):

        start_epoch_time = int(time.time())
        oldest_game = start_epoch_time - (3600 * int(options['oldest_age']))

        # establish MongoDB connection
        db_name = 'aoe2db'
        host = 'localhost'
        port = 27017
        username = os.environ.get('MONGODB_USERNAME')
        password = os.environ.get('MONGODB_PASSWORD')
        db_handle, client = get_db_handle(db_name, host, port, username, password)

        batch_size = options['batch_size']
        games_queryset = Game.objects.filter(downloaded=0, start_time__gt=oldest_game)
        games_iterator = games_queryset.iterator()
        batch_num = 0
        failed_counter = 0
        success_counter = 0
        attempts_counter = 0
        global_wait_time = 0
        print(f"current time: {start_epoch_time}")
        print(f"oldest game will be at time: {oldest_game}")

        prev_iteration_epoch_time = start_epoch_time
        while True:
            iteration_start_epoch_time = time.time()
            total_elapsed_epoch_time = iteration_start_epoch_time - start_epoch_time
            iteration_elapsed_epoch_time = iteration_start_epoch_time - prev_iteration_epoch_time
            batch = list(islice(games_iterator, batch_size))
            print(f"batch: {batch_num}")
            print(f"Total Attempts: {attempts_counter}")
            print(f"Total Successes: {success_counter}")
            print(f"Total Fails: {failed_counter}")
            print(f"Prev iteration elapsed time: {iteration_elapsed_epoch_time}")
            print(f"Total elapsed time: {total_elapsed_epoch_time}")
            print(f"Total time spent waiting(429s): {global_wait_time}")
            if not batch:
                break
            game_ids = [game.game_id for game in batch]
            print(f"game_ids: {game_ids}\n")
            batch_num += 1
            for game in batch:
                wait_time = 2
                game_file_compressed, status_code = self.download_game_file(game.game_id, game.creator_profile_id)
                while(wait_time < 17 and status_code == 429): # wait and retry 429 errors
                    global_wait_time += wait_time
                    time.sleep(wait_time)
                    game_file_compressed, status_code = self.download_game_file(game.game_id, game.creator_profile_id)
                    wait_time *= 2
                if status_code is 403: # 403 error
                    failed_counter += 1
                    attempts_counter += 1
                    game.downloaded = 4
                    game.save(update_fields=['downloaded'])
                    continue
                if status_code is 429: # 429 error
                    failed_counter += 1
                    attempts_counter += 1
                    game.downloaded = 3
                    game.save(update_fields=['downloaded'])
                    continue
                if status_code is  404: # 404 error
                    failed_counter += 1
                    attempts_counter += 1
                    game.downloaded = 2
                    game.save(update_fields=['downloaded'])
                    continue
                if status_code is not 200: # other error
                    failed_counter += 1
                    attempts_counter += 1
                    game.downloaded = 5
                    game.save(update_fields=['downloaded'])
                    continue
                decompressed = self.decompress(game_file_compressed)
                json_dump = self.replay_parser(decompressed)
                success_counter += self.insert_into_mongodb(game.game_id, json_dump, db_handle)
                attempts_counter += 1
                game.downloaded = 1
                game.save(update_fields=['downloaded'])

            prev_iteration_epoch_time = iteration_start_epoch_time
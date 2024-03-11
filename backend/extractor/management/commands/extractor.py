import os
import json
from django.core.management.base import BaseCommand
from pymongo import MongoClient

class Command(BaseCommand):
    help = 'Load player information from parsed JSON files into MongoDB'

    def handle(self, *args, **options):
        # MongoDB connection settings
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aoe2db']
        collection = db['matches']

        parsed_files_directory = '/home/chad/aoe2outpost/parsedfiles'

        # Iterate over each file in the directory
        for filename in os.listdir(parsed_files_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(parsed_files_directory, filename)
                self.process_file(file_path, collection, filename)

        client.close()

    def process_file(self, file_path, collection, filename):
        # Open and load JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract match information
        match_info = self.extract_match_info(data, filename)

        # Insert match information into MongoDB collection
        if match_info:
            collection.insert_one(match_info)
            self.stdout.write(self.style.SUCCESS(f"Inserted match information from {filename} into MongoDB."))
        else:
            self.stdout.write(self.style.WARNING(f"Skipping {filename}: Match does not have exactly 2 players."))

    def extract_match_info(self, data, filename):
        # Extract required information from JSON data
        players = data.get('players', [])
        if len(players) == 2:
            player1 = players[0]
            player2 = players[1]

            # Look for the timestamp when Loom is researched
            p1_loom = self.get_loom_time(data, player1['number'])
            p2_loom = self.get_loom_time(data, player2['number'])

            match_info = {
                'filename': filename,
                'player1': {
                    'name': player1.get('name'),
                    'rating': player1.get('rate_snapshot'),
                    'civilization': player1.get('civilization'),
                    'loom_research_time': p1_loom
                },
                'player2': {
                    'name': player2.get('name'),
                    'rating': player2.get('rate_snapshot'),
                    'civilization': player2.get('civilization'),
                    'loom_research_time': p2_loom
                }
            }
            return match_info
        else:
            return None

    def get_loom_time(self, data, number):
        actions = data.get('actions', [])
        for action in actions:
            if action['player'] == number and action['type'] == 'RESEARCH' and action['payload']['technology_id'] == 22:
                loom_research_time = action['timestamp']
                return loom_research_time

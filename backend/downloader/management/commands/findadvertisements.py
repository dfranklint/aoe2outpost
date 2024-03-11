from django.core.management.base import BaseCommand
import requests
import json
import os

class Command(BaseCommand):
    help = 'Fetch advertisements and save player and game IDs to a JSON file'

    def fetch_matches(self):
        url = "https://aoe-api.reliclink.com/community/advertisement/findAdvertisements?title=age2"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["matches"]
        else:
            self.stdout.write(self.style.ERROR(f"Failed to fetch matches: {response.status_code}"))
            return None

    def extract_player_game_ids(self, matches):
        player_game_ids = []
        if matches:
            for match in matches:
                playerid = match.get("playerid")
                gameid = match.get("gameid")
                if playerid and gameid:
                    player_game_ids.append({"playerid": playerid, "gameid": gameid})
        return player_game_ids

    def save_to_json(self, data, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as json_file:
            json.dump(data, json_file, indent=4)

    def handle(self, *args, **options):
        matches = self.fetch_matches()
        if matches:
            player_game_ids = self.extract_player_game_ids(matches)
            self.save_to_json(player_game_ids, "/home/chad/aoe2outpost/advertisements/player_game_ids.json")
            self.stdout.write(self.style.SUCCESS('Successfully saved player and game IDs to player_game_ids.json'))
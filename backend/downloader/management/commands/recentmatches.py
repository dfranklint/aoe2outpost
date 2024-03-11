from django.core.management.base import BaseCommand
import requests
import json
import os

class Command(BaseCommand):
    help = 'Fetches recent matches for players within a specified rank range'

    def add_arguments(self, parser):
        parser.add_argument('start_rank', type=int, help='Starting rank for players')
        parser.add_argument('end_rank', type=int, help='Ending rank for players')

    def fetch_recent_matches(self, profile_name):
        url = f"https://aoe-api.reliclink.com/community/leaderboard/getRecentMatchHistory?title=age2&profile_names=[%22{profile_name}%22]"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch recent matches for {profile_name}: {response.status_code}")
            return None

    def extract_game_data(self, match):
        if match.get("maxplayers") == 2 and match.get("description") == "AUTOMATCH":
            game_id = match.get("id")
            player_data = []
            for member in match.get("matchhistorymember", []):
                player_data.append({
                    "profile_id": member.get("profile_id"),
                    "race_id": member.get("race_id"),
                    "outcome": member.get("outcome")
                })
            return {"game_id": game_id, "players": player_data}
        else:
            return None

    def handle(self, *args, **options):
        start_rank = options['start_rank']
        end_rank = options['end_rank']

        leaderboard_file = "/home/chad/aoe2outpost/leaderboard/leaderboard.json"
        recent_matches_file = "/home/chad/aoe2outpost/recentmatches/recentmatches.json"

        recent_matches = {}
        with open(leaderboard_file, "r") as f:
            leaderboard_data = json.load(f)

        for entry in leaderboard_data:
            rank = entry.get("rank")
            if start_rank <= rank <= end_rank:
                profile_name = entry.get("name")
                recent_match_data = self.fetch_recent_matches(profile_name)
                if recent_match_data:
                    matches = recent_matches.get(profile_name, [])
                    for match in recent_match_data.get("matchHistoryStats", []):
                        game_data = self.extract_game_data(match)
                        if game_data:
                            matches.append(game_data)
                    recent_matches[profile_name] = matches

        with open(recent_matches_file, "w") as f:
            json.dump(recent_matches, f, indent=4)

        print(f"Recent matches saved to {recent_matches_file}")
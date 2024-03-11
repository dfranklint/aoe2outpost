from django.core.management.base import BaseCommand
import requests
import json
import os

class Command(BaseCommand):
    help = 'Fetch leaderboard data and save to JSON file'

    def fetch_rank_total(self):
        url = "https://aoe-api.reliclink.com/community/leaderboard/getLeaderBoard2?leaderboard_id=3&platform=PC_STEAM&title=age2&sortBy=1&start=1&count=1"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rank_total = data.get("rankTotal")
            return rank_total
        else:
            self.stdout.write(self.style.ERROR(f"Failed to fetch rank_total: {response.status_code}"))
            return None

    def fetch_leaderboard(self, start):
        url = f"https://aoe-api.reliclink.com/community/leaderboard/getLeaderBoard2?leaderboard_id=3&platform=PC_STEAM&title=age2&sortBy=1&start={start}&count=200"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            self.stdout.write(self.style.ERROR(f"Failed to fetch leaderboard for start={start}: {response.status_code}"))
            return None

    def extract_data(self, response):
        leaderboard_stats = response.get("leaderboardStats", [])
        stat_groups = response.get("statGroups", [])

        extracted_data = []
        for stat in leaderboard_stats:
            player_id = stat.get("statgroup_id")
            player_data = {
                "rank": stat.get("rank"),
                "wins": stat.get("wins"),
                "losses": stat.get("losses"),
                "rating": stat.get("rating"),
                "lastmatchdate": stat.get("lastmatchdate")
            }
            for group in stat_groups:
                if group.get("id") == player_id:
                    player_data["profile_id"] = group["members"][0].get("profile_id")
                    player_data["name"] = group["members"][0].get("name")
                    player_data["alias"] = group["members"][0].get("alias")
                    break
            extracted_data.append(player_data)

        return extracted_data

    def save_to_json(self, data, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "a") as json_file:
            json.dump(data, json_file, indent=4)
            json_file.write("\n")  # Add newline between each JSON object

    def handle(self, *args, **options):
        rank_total = self.fetch_rank_total()
        if rank_total is None:
            return

        start_values = range(1, rank_total + 1, 200)  # Adjust range as needed
        all_extracted_data = []

        for start in start_values:
            response = self.fetch_leaderboard(start)
            if response:
                extracted_data = self.extract_data(response)
                all_extracted_data.extend(extracted_data)
                self.stdout.write(self.style.SUCCESS(f"Data for start={start} fetched"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to fetch data for start={start}"))

        # Write all the extracted data to the JSON file
        self.save_to_json(all_extracted_data, "/home/chad/aoe2outpost/leaderboard/leaderboard.json")
        self.stdout.write(self.style.SUCCESS("All data saved to leaderboard.json"))
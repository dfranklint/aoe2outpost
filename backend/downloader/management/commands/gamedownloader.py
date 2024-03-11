from django.core.management.base import BaseCommand
import requests
import json
import os

class Command(BaseCommand):
    help = 'Download game files from API and update successful and unsuccessful downloads'

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

    def download_game_file(self, game_id, profile_id):
        url = f"https://aoe.ms/replay/?gameId={game_id}&profileId={profile_id}"
        headers = {'User-Agent': self.USER_AGENT}
        self.stdout.write(f"Sending request to download game file for game_id={game_id}, profile_id={profile_id}")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.stdout.write(f"Game file downloaded successfully for game_id={game_id}")
        else:
            self.stdout.write(f"Failed to download game file for game_id={game_id}. Status code: {response.status_code}")
            # Log the content of the response
            self.stdout.write(f"Response content: {response.content}")

        return response.content if response.status_code == 200 else None

    def handle(self, *args, **options):
        recent_matches_file = "/home/chad/aoe2outpost/recentmatches/recentmatches.json"
        successful_downloads_file = "/home/chad/aoe2outpost/successfuldownloads.txt"
        unsuccessful_downloads_file = "/home/chad/aoe2outpost/unsuccessfuldownloads.txt"
        game_files_directory = "/home/chad/aoe2outpost/gamefiles/"

        with open(recent_matches_file, "r") as f:
            recent_matches_data = json.load(f)

        old_successful_downloads = []
        old_unsuccessful_downloads = []
        new_successful_downloads = []
        new_unsuccessful_downloads = []
        downloads_unattempted = 0

        # Read game ids from successfuldownloads.txt and unsuccessfuldownloads.txt
        with open(successful_downloads_file, "r") as f:
            old_successful_downloads.extend(line.strip() for line in f)

        with open(unsuccessful_downloads_file, "r") as f:
            old_unsuccessful_downloads.extend(line.strip() for line in f)

        for profile_name, matches in recent_matches_data.items():
            for match in matches:
                game_id = match["game_id"]
                if str(game_id) not in old_successful_downloads and str(game_id) not in old_unsuccessful_downloads:
                    profile_id = match["players"][0]["profile_id"]  # Assuming the first player's profile_id
                    game_file = self.download_game_file(game_id, profile_id)
                    if game_file:
                        # Save the game file
                        file_path = os.path.join(game_files_directory, f"{game_id}.aoe2record.zip")
                        with open(file_path, "wb") as game_file_handle:
                            game_file_handle.write(game_file)
                        new_successful_downloads.append(str(game_id))
                    else:
                        new_unsuccessful_downloads.append(str(game_id))
                else:
                    downloads_unattempted += 1
                    self.stdout.write(f"Request not sent for game_id {game_id}.")

        # Update successful downloads file
        with open(successful_downloads_file, "a") as f:
            f.write("\n".join(new_successful_downloads))

        # Update unsuccessful downloads file
        with open(unsuccessful_downloads_file, "a") as f:
            f.write("\n".join(new_unsuccessful_downloads))

        self.stdout.write(f"Downloaded {len(new_successful_downloads)} game files successfully.")
        self.stdout.write(f"Failed to download {len(new_unsuccessful_downloads)} game files.")
        self.stdout.write(f"{downloads_unattempted} downloads not attempted.")
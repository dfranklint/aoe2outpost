# Inside your_app/management/commands/fetch_data.py

import os
import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Fetch recent match history data from the API'

    def handle(self, *args, **options):
        api_url = 'https://aoe-api.reliclink.com/community/leaderboard/getRecentMatchHistory'
        profile_ids = ["6308095"]  # Replace with your desired profile IDs

        # Construct request parameters
        params = {
            'title': 'age2',
            'profile_ids': json.dumps(profile_ids)
        }

        # Send API request
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            data = response.json()

            # Save JSON response locally
            file_path = '/home/chad/aoe2outpost/recentmatchhistories/newfile.json'
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)

            self.stdout.write(self.style.SUCCESS('Recent match history data fetched and saved successfully'))
        else:
            self.stderr.write(self.style.ERROR('Failed to fetch recent match history data from API'))
            self.stderr.write(self.style.ERROR(f'Response content: {response.content.decode()}'))
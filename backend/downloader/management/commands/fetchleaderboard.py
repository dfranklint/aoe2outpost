from django.core.management.base import BaseCommand
from downloader.models import Player, PlayerSnapshot
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
        diplomacy_type = 1 # 1 for 1v1 ladder

        for stat in leaderboard_stats:
            statgroup_id = stat.get("statgroup_id")
            print(statgroup_id)
            wins = stat.get("wins")
            losses = stat.get("losses")
            streak = stat.get("streak")
            drops = stat.get("drops")
            rank = stat.get("rank")
            rating = stat.get("rating")
            lastmatchdate = stat.get("lastmatchdate")
            print(lastmatchdate)

            for group in stat_groups:
                if group.get("id") == statgroup_id:
                    member = group["members"][0]

            profile_id = member.get("profile_id")
            name = member.get("name")
            alias = member.get("alias")
            print(alias)

            # Create or update Player instance
            player, created = Player.objects.get_or_create(profile_id=profile_id)

            if created:
                print("New player created.")
                player.name = name
                player.alias = alias
                player.save()
            else:
                print("Player already exists.")

            # Create PlayerSnapshot instance
            player_snapshot, created = PlayerSnapshot.objects.get_or_create(
                profile_id=profile_id,
                diplomacy_type=diplomacy_type,
                lastmatchdate=lastmatchdate
            )

            if created:
                print("New playersnapshot created.")
                player_snapshot.wins = wins
                player_snapshot.losses = losses
                player_snapshot.streak = streak
                player_snapshot.drops = drops
                player_snapshot.rank = rank
                player_snapshot.rating = rating
                player_snapshot.lastmatchdate = lastmatchdate
                player_snapshot.diplomacy_type = diplomacy_type
                player_snapshot.save()
            else:
                print("Player snapshot already exists.")

        return

    def handle(self, *args, **options):
        rank_total = self.fetch_rank_total()
        if rank_total is None:
            return

        start_values = range(1, rank_total + 1, 200)

        for start in start_values:
            response = self.fetch_leaderboard(start)
            if response:
                self.stdout.write(self.style.SUCCESS(f"Data for start={start} fetched"))
                self.extract_data(response)
            else:
                self.stdout.write(self.style.ERROR(f"Failed to fetch data for start={start}"))
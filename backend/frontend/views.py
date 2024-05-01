from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from downloader.models import GamePlayer, GamePlayerMetadata
import json
import numpy as np
from scipy.stats import scoreatpercentile
import random


from datetime import timedelta
from collections import Counter

def duration_to_seconds(duration):
    if duration is None:
        return None
    return duration.total_seconds()

def index(request):
    return render(request, 'base.html')

def scatter_plots(request):
    if request.method == 'POST':
        min_elo = int(request.POST.get('min_elo') or '0')
        max_elo = int(request.POST.get('max_elo') or '3000')
        tech1 = request.POST.get('tech1')
        tech2 = request.POST.get('tech2')
        num_points = int(request.POST.get('num_points') or '1000')
        title = f"{tech1} vs {tech2}"

        # Filter GamePlayerMetadata queryset based on min_elo and max_elo
        filtered_objects = GamePlayerMetadata.objects.filter(rating__gte=min_elo, rating__lte=max_elo)

        # Randomly select num_points from the filtered queryset
        selected_objects = random.sample(list(filtered_objects), num_points)

        # Extract tech1 and tech2 for each selected point and structure data points
        data_points = []
        for obj in selected_objects:
            if tech1.endswith("_timing"):
                tech1_datapoint = duration_to_seconds(getattr(obj, tech1))
            else:
                tech1_datapoint = getattr(obj, tech1)

            if tech2.endswith("_timing"):
                tech2_datapoint = duration_to_seconds(getattr(obj, tech2))
            else:
                tech2_datapoint = getattr(obj, tech2)

            data_point = {
                'tech1': tech1_datapoint,
                'tech2': tech2_datapoint
            }
            data_points.append(data_point)

            if tech1.endswith("_timing"):
                tech1_label = tech1 + " (seconds)"
            else:
                tech1_label = tech1

            if tech2.endswith("_timing"):
                tech2_label = tech1 + " (seconds)"
            else:
                tech2_label = tech2

        # Return data points in JSON format
        return JsonResponse({
            'data_points': data_points,
            'x_label': tech1_label,
            'y_label': tech2_label,
            'title': title
        })

    return render(request, 'scatter_plots.html')




def line_charts(request):
    if request.method == 'POST':
        min_elo = int(request.POST.get('min_elo') or '0')
        max_elo = int(request.POST.get('max_elo') or '3000')
        tech = request.POST.get('tech')
        num_lines = int(request.POST.get('num_lines') or '5')
        max_duration_hours = int(request.POST.get('max_duration_hours') or '0')
        max_duration_minutes = int(request.POST.get('max_duration_minutes') or '0')
        intervals_minutes = int(request.POST.get('intervals_minutes') or '0')
        intervals_seconds = int(request.POST.get('intervals_seconds') or '0')
        minimum_duration_seconds = int(request.POST.get('min_duration_seconds') or '0')  # Add this line

        tech_field_name = f"{tech}"

        # Convert intervals and max duration to seconds
        max_duration_seconds = max_duration_hours * 3600 + max_duration_minutes * 60
        intervals_seconds = intervals_minutes * 60 + intervals_seconds

        intervals = []
        for interval in range(minimum_duration_seconds, max_duration_seconds + 1, intervals_seconds): # for each time interval
            intervals.append(interval)

        # Calculate line width and initialize lines
        line_width = (max_elo - min_elo) / num_lines
        lines = [[] for _ in range(num_lines)]

        # Initialize a list to store the percentages
        labels = []

        # Iterate over each interval
        for i, line in enumerate(lines): # for each elo range
            elo_min = round(min_elo + i * line_width)
            elo_max = round(min_elo + (i + 1) * line_width)
            labels.append(f"{elo_min}-{elo_max}")  # Create label for elo range
            elo_range_gpm_count = GamePlayerMetadata.objects.filter(rating__gte=elo_min, rating__lte=elo_max).count()
            print(f"elo range gpm count: {elo_range_gpm_count}")
            for interval in range(minimum_duration_seconds, max_duration_seconds + 1, intervals_seconds): # for each time interval
                print(f"interval {interval}")
                #Filter by elo range and tech timing less than this interval
                td_interval = timedelta(seconds=interval)
                filtered_objects_count = GamePlayerMetadata.objects.filter(**{f"{tech_field_name}__lte": td_interval}, rating__gte=elo_min, rating__lte=elo_max).count()
                print(f"filtered objects count {filtered_objects_count}")
                # Calculate the percentage
                percentage = (filtered_objects_count / elo_range_gpm_count) * 100
                # Append the percentage to the list
                lines[i].append(percentage)
                print(f"{percentage} added to {i} element number {interval}")

        for label in labels:
            print(f"label {label}")

        for line in lines:
            print(f"line {line}")
            for percentage in line:
                print(f"percentage: {percentage}")

        # Return data in the format expected by JavaScript
        return JsonResponse({
            'labels': labels,
            'lines': lines,
            'intervals': intervals,
            'tech': tech
        })

    return render(request, 'line_charts.html')

def box_plots(request):
    if request.method == 'POST':
        min_elo = int(request.POST.get('min_elo') or '0') # default to 1000 if no value given
        max_elo = int(request.POST.get('max_elo') or '3000')
        tech = request.POST.get('tech')
        num_bins = int(request.POST.get('num_bins') or '10')
        game_player_metadatas = GamePlayerMetadata.objects.filter(rating__gte=min_elo, rating__lte=max_elo)

        # Calculate bin width and initialize bins
        bin_width = (max_elo - min_elo) / num_bins
        bins = [[] for _ in range(num_bins)]

        # Populate bins with data
        for metadata in game_player_metadatas:
            if min_elo <= metadata.rating <= max_elo:
                tech_timing = getattr(metadata, f'{tech}')
                seconds = duration_to_seconds(tech_timing)
                bin_index = int((metadata.rating - min_elo) // bin_width)
                if bin_index < num_bins:
                    bins[bin_index].append(seconds)

        # Calculate percentile values for each bin
        medians = []
        p75s = []
        p25s = []
        p10s = []
        p90s = []
        bin_labels = []

        for i, bin_data in enumerate(bins):
            bin_data = [value for value in bin_data if value is not None]
            if bin_data:
                elo_min = round(min_elo + i * bin_width)
                elo_max = round(min_elo + (i + 1) * bin_width)
                bin_labels.append(f"{elo_min}-{elo_max}")  # Create label for elo range
                medians.append(np.median(bin_data))
                p75s.append(scoreatpercentile(bin_data, 75))
                p25s.append(scoreatpercentile(bin_data, 25))
                p10s.append(scoreatpercentile(bin_data, 10))
                p90s.append(scoreatpercentile(bin_data, 90))
            else:
                bin_labels.append(None)
                medians.append(None)
                p75s.append(None)
                p25s.append(None)
                p10s.append(None)
                p90s.append(None)

        # Return data in the format expected by JavaScript
        return JsonResponse({
            'labels': bin_labels,  # Bin labels as elo ranges
            'medians': medians,
            'p75s': p75s,
            'p25s': p25s,
            'p10s': p10s,
            'p90s': p90s,
            'tech': tech
        })

    return render(request, 'box_plots.html')



#def box_plots(request): # returns box plot datapoints for 20 slices of elos based on min and max provided elos
#    if request.method == 'POST':
#        min_elo = int(request.POST.get('min_elo'))
#        max_elo = int(request.POST.get('max_elo'))
#        tech = request.POST.get('tech')
#
#        print(f"getting GamePlayerMetadata.objects.all()")
#
#        game_player_metadatas = GamePlayerMetadata.objects.filter(rating__gte=min_elo, rating__lte=max_elo)
#
#        # Calculate bin width and initialize bins
#        bin_width = (max_elo - min_elo) / 20
#        bins = [[] for _ in range(20)]
#        print(f"doing for metadata in game_player_metadatas: ")
#        for metadata in game_player_metadatas:
#            if min_elo <= metadata.rating <= max_elo:
#                tech_timing = getattr(metadata, f'{tech}_timing')
#                # Convert tech timing to seconds
#                seconds = duration_to_seconds(tech_timing)
#                # Find which bin the data point belongs to
#                bin_index = int((metadata.rating - min_elo) // bin_width)
#                # Add the timing to the bin
#                if bin_index < 20:
#                    bins[bin_index].append(seconds)
#
#        # Initialize lists to store percentile data for each bin
#        medians = []
#        p75s = []
#        p25s = []
#        p10s = []
#        p90s = []
#
#        print(f"doing for bin_data in bins:")
#        # Calculate percentile values for each bin
#        for bin_data in bins:
#            # Filter out None values from bin_data
#            bin_data = [value for value in bin_data if value is not None]
#            if bin_data:
#                medians.append(np.median(bin_data))
#                p75s.append(scoreatpercentile(bin_data, 75))
#                p25s.append(scoreatpercentile(bin_data, 25))
#                p10s.append(scoreatpercentile(bin_data, 10))
#                p90s.append(scoreatpercentile(bin_data, 90))
#            else:
#                # If no data in the bin, add NaN values
#                medians.append(np.nan)
#                p75s.append(np.nan)
#                p25s.append(np.nan)
#                p10s.append(np.nan)
#                p90s.append(np.nan)
#
#        # Return data in the format expected by JavaScript
#        return JsonResponse({
#            'labels': list(range(1, 21)),  # Bin indices
#            'medians': medians,
#            'p75s': p75s,
#            'p25s': p25s,
#            'p10s': p10s,
#            'p90s': p90s
#        })
#
#    return render(request, 'box_plots.html')
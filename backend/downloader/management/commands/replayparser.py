import os
import json
import zipfile
from django.core.management.base import BaseCommand
from mgz.model import parse_match, serialize

class Command(BaseCommand):
    help = 'Parse replay files and save the output as JSON'

    def handle(self, *args, **options):
        input_directory = '/home/chad/aoe2outpost/gamefiles'
        output_directory = '/home/chad/aoe2outpost/parsedfiles'

        # Create the output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Iterate over files in the input directory
        for filename in os.listdir(input_directory):
            if filename.endswith('.zip'):
                input_file_path = os.path.join(input_directory, filename)

                # Extract the contents of the ZIP archive
                with zipfile.ZipFile(input_file_path, 'r') as zip_ref:
                    # Iterate over files in the ZIP archive
                    for extracted_file in zip_ref.namelist():
                        if extracted_file.endswith('.aoe2record'):
                            # Read the file directly from the archive
                            with zip_ref.open(extracted_file, 'r') as f:
                                # Parse the match
                                match = parse_match(f)
                                serialized_data = serialize(match)

                                # Save the serialized data to a JSON file in the output directory
                                output_json_file_path = os.path.join(output_directory, f'{extracted_file}.json')
                                with open(output_json_file_path, 'w') as json_file:
                                    json.dump(serialized_data, json_file, indent=2)

                                self.stdout.write(f"Processed {extracted_file}.")
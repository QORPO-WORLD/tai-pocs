import os
from collections import defaultdict

from pydub import AudioSegment

# Configuration
# Directory where the MP3 files are located
input_directory = "/Users/akim/repos/QORPO/taix-infra/src/output/audio/amazon.nova-pro-v1:0-0.9-3-1-10/30-70"
output_directory = "/Users/akim/repos/QORPO/taix-infra/src/output/audio/amazon.nova-pro-v1:0-0.9-3-1-10/30-70/merged"
silence_duration = 10000  # 10 seconds in milliseconds

os.makedirs(output_directory, exist_ok=True)

# Group files by timestamp
file_groups = defaultdict(list)
for filename in os.listdir(input_directory):
    if filename.endswith(".mp3"):
        timestamp = filename.split("-")[0]  # Extract the timestamp
        file_groups[timestamp].append(os.path.join(input_directory, filename))

# Process each group
for timestamp, files in file_groups.items():
    combined = AudioSegment.silent(duration=0)

    # Merge all files in the group
    for file in sorted(files):  # Sort to maintain order
        audio = AudioSegment.from_mp3(file)
        combined += audio

    # Save the merged file
    output_path = os.path.join(output_directory, f"{timestamp}.mp3")
    combined.export(output_path, format="mp3")
    print(f"Saved: {output_path}")

# Create a 10-second silence file
silence = AudioSegment.silent(duration=silence_duration)
silence_path = os.path.join(output_directory, "silence_10s.mp3")
silence.export(silence_path, format="mp3")
print(f"Saved silence file: {silence_path}")

print("Processing complete!")

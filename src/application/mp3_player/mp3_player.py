import os
import time
import datetime
import pygame

def play_mp3_files_in_sequence(folder_path, initial_unix_timestamp):
    pygame.mixer.init()  # Initialize the mixer

    # Convert initial Unix timestamp to a datetime object
    initial_time = datetime.datetime.fromtimestamp(initial_unix_timestamp)

    # Get all mp3 files in the folder
    mp3_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]

    # Extract and sort files by Unix timestamp
    mp3_files_with_timestamps = []
    for mp3_file in mp3_files:
        # Extract the timestamp from the filename (assumes format: "<unix_timestamp>-<index>.mp3")
        timestamp_str = os.path.splitext(mp3_file)[0].split('-')[0]
        try:
            timestamp = int(timestamp_str)
            mp3_files_with_timestamps.append((timestamp, mp3_file))
        except ValueError:
            print(f"Skipping {mp3_file}: invalid timestamp format.")
            continue

    # Sort files by timestamp
    mp3_files_with_timestamps.sort()

    # Iterate over each file and play it at the correct time
    current_time = initial_time
    for timestamp, mp3_file in mp3_files_with_timestamps:
        file_time = datetime.datetime.fromtimestamp(timestamp)

        # Calculate the difference between initial time and file time
        time_difference = (file_time - current_time).total_seconds()

        # If time difference is positive, wait until the correct time
        if time_difference > 0:
            print(f"Waiting {time_difference:.2f} seconds for {mp3_file}...")
            time.sleep(time_difference)

        # Play the file
        print(f"Playing {mp3_file} at {datetime.datetime.now().time()}")
        pygame.mixer.music.load(os.path.join(folder_path, mp3_file))
        pygame.mixer.music.play()

        # Wait until the audio finishes
        while pygame.mixer.music.get_busy():
            time.sleep(1)

        # Update current time to match the file time
        current_time = file_time

if __name__ == "__main__":
    # Example usage
    folder_path = "samples"  # Replace with your folder path
    initial_unix_timestamp = 1739551230  # Replace with your initial Unix timestamp
    play_mp3_files_in_sequence(folder_path, initial_unix_timestamp)

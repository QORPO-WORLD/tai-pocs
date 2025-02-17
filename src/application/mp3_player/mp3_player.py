import os
import time
import datetime
import random
import pygame

def play_mp3_files_with_deltas(folder_path, initial_unix_timestamp):
    pygame.mixer.init()  # Initialize the mixer

    script_start_timestamp = int(time.time())

    # Get all mp3 files in the folder
    mp3_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]

    # Group files by timestamp and randomize indices within each timestamp
    mp3_files_by_timestamp = {}
    for mp3_file in mp3_files:
        # Extract the timestamp from the filename (assumes format: "<unix_timestamp>-<index>.mp3")
        timestamp_str = os.path.splitext(mp3_file)[0].split('-')[0]
        try:
            timestamp = int(timestamp_str) - initial_unix_timestamp
            if timestamp not in mp3_files_by_timestamp:
                mp3_files_by_timestamp[timestamp] = []
            mp3_files_by_timestamp[timestamp].append(mp3_file)
        except ValueError:
            print(f"Skipping {mp3_file}: invalid timestamp format.")
            continue

    # Sort timestamps in ascending order
    sorted_timestamps = sorted(mp3_files_by_timestamp.keys())

    # Shuffle the files for each timestamp as a preprocessing step
    for timestamp in sorted_timestamps:
        random.shuffle(mp3_files_by_timestamp[timestamp])

    next_timestamp_logged = False  # Track if the next timestamp has been logged
    current_timestamp_record_index = 0
    old_valid_timestamp = None

    while True:
        # Calculate the current timestamp using the interval of 3 seconds
        interval = 10
        current_timestamp = (int(time.time() - script_start_timestamp) // interval) * interval

        # Find the closest timestamp less than or equal to the current timestamp
        valid_timestamp = None
        for timestamp in sorted_timestamps:
            if timestamp <= current_timestamp:
                valid_timestamp = timestamp
            else:
                break

        if valid_timestamp is None:
            print("No more messages to play. Ending.")
            break

        # If a new valid timestamp is reached, reset the index after finishing the current playback
        if valid_timestamp != old_valid_timestamp:
            if old_valid_timestamp is not None and pygame.mixer.music.get_busy():
                # Allow the current recording to finish before switching
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            current_timestamp_record_index = 0
            old_valid_timestamp = valid_timestamp

        # Play the next file in the current timestamp
        records_list = mp3_files_by_timestamp[valid_timestamp]
        if current_timestamp_record_index >= len(records_list):
            print(f"Reached the end of records for timestamp {valid_timestamp}.")
            # Remove the played timestamp from the dictionary and the sorted list
            break

        mp3_file = records_list[current_timestamp_record_index]
        print(f"Playing {mp3_file} at {datetime.datetime.now().time()}")
        pygame.mixer.music.load(os.path.join(folder_path, mp3_file))
        pygame.mixer.music.play()

        # Wait until the audio finishes
        while pygame.mixer.music.get_busy():
            elapsed_time_since_start = int(time.time()) - script_start_timestamp
            if not next_timestamp_logged and elapsed_time_since_start >= valid_timestamp:
                print(f"Next timestamp {valid_timestamp} reached. Will switch after current playback...")
                next_timestamp_logged = True
            time.sleep(0.1)

        # Move to the next file in the current timestamp
        current_timestamp_record_index += 1
        next_timestamp_logged = False  # Reset flag for the next timestamp

if __name__ == "__main__":
    # Example usage
    folder_path = "30-70"  # Replace with your folder path
    initial_unix_timestamp = 1739551230  # Set this to the initial time (e.g., first timestamp in your batch)
    play_mp3_files_with_deltas(folder_path, initial_unix_timestamp)

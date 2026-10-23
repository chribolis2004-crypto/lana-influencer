import pandas as pd
from datetime import datetime
import os
import argparse
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Multi-influencer Publisher")
    parser.add_argument("--creator", type=str, required=True, help="Name of the creator to publish for")
    parser.add_argument("--force", action="store_true", help="Force all ready assets")
    return parser.parse_args()

def run_publisher(creator_name, force_all=False):
    # Setup paths
    creator_path = os.path.join("creators", creator_name)
    calendar_path = os.path.join(creator_path, "calendar.csv")
    config_path = os.path.join(creator_path, "config.json")

    try:
        df = pd.read_csv(calendar_path)
    except FileNotFoundError:
        print(f"Content calendar not found for creator {creator_name}.")
        return

    # Load API keys for the creator
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        api_keys = config.get("api_keys", {})
    except Exception as e:
        print(f"Error loading config for {creator_name}: {e}")
        api_keys = {}

    now = datetime.now()
    published_count = 0

    for index, row in df.iterrows():
        # Criteria: Final QA Approval, Ready (Image exists), and still in Draft
        if (row['qa_stage'] == 'final' and
            row['production_status'] == 'ready' and
            row['publish_status'] == 'draft'):

            # Date verification
            publish_date_str = str(row['date'])
            try:
                publish_date = datetime.strptime(publish_date_str, '%Y-%m-%d')
                if not force_all and now < publish_date:
                    continue # Not yet time to publish
            except ValueError:
                print(f"Invalid date format for row {index}: {publish_date_str}")
                continue

            # Actual Publishing logic would go here using api_keys
            print(f"Publishing {row['content_id']} for {creator_name}...")
            print(f"  - Asset: {row['image_path']}")
            print(f"  - Caption: {row['caption']}")
            print(f"  - Format: {row['format']}")
            print(f"  - Using keys: {list(api_keys.keys())}")

            # Simulate successful API call
            df.at[index, 'publish_status'] = 'published'
            df.at[index, 'published_at'] = now.strftime('%Y-%m-%d %H:%M:%S')
            published_count += 1

    df.to_csv(calendar_path, index=False)
    print(f"Publisher process completed for {creator_name}. {published_count} posts published.")

if __name__ == "__main__":
    args = parse_args()
    run_publisher(args.creator, force_all=args.force)

import pandas as pd
from datetime import datetime
import os

def run_publisher(force_all=False):
    try:
        df = pd.read_csv('content_calendar.csv')
    except FileNotFoundError:
        print("Content calendar not found.")
        return

    now = datetime.now()
    published_count = 0

    for index, row in df.iterrows():
        # Criteria: Approved, Ready (Image exists), and still in Draft
        if (row['qa_status'] == 'approved' and
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

            # Simulation of Publishing
            # In a real scenario, this would call Instagram/TikTok API
            print(f"Publishing {row['content_id']}...")
            print(f"  - Asset: {row['image_path']}")
            print(f"  - Caption: {row['caption']}")
            print(f"  - Format: {row['format']}")

            # Simulate successful API call
            df.at[index, 'publish_status'] = 'published'
            df.at[index, 'published_at'] = now.strftime('%Y-%m-%d %H:%M:%S')
            published_count += 1

    df.to_csv('content_calendar.csv', index=False)
    print(f"Publisher process completed. {published_count} posts published.")

if __name__ == "__main__":
    import sys
    force = '--force' in sys.argv
    run_publisher(force_all=force)

import pandas as pd

def run_qa_check():
    try:
        df = pd.read_csv('content_calendar.csv')
    except FileNotFoundError:
        print("Content calendar not found.")
        return

    # Basic requirements
    required_fields = ['hook', 'caption', 'format', 'visual_prompt']

    results = []
    for index, row in df.iterrows():
        notes = []
        status = 'approved'

        # Check completeness
        for field in required_fields:
            if pd.isna(row[field]) or str(row[field]).strip() == "":
                notes.append(f"Missing {field}")
                status = 'rejected'

        # Check Brand Bible compliance (Simple check: visual prompt must contain 'Lana' style cues)
        # In a real scenario, this would be more complex.
        if 'visual_prompt' in row and not any(keyword in str(row['visual_prompt']) for keyword in ['Minimalist', 'Neutral', 'Lana']):
            notes.append("Visual prompt does not align with Brand Bible")
            status = 'rejected'

        # Disclosure check (Simplified: check if caption mentions AI or Ads if product exists)
        if pd.notna(row['product_id']) and row['product_id'] != "":
            if "ad" not in str(row['caption']).lower() and "partner" not in str(row['caption']).lower():
                notes.append("Missing affiliate disclosure in caption")
                status = 'rejected'

        df.at[index, 'qa_status'] = status
        df.at[index, 'qa_notes'] = "; ".join(notes)

    df.to_csv('content_calendar.csv', index=False)
    print("QA Gate process completed.")

if __name__ == "__main__":
    run_qa_check()

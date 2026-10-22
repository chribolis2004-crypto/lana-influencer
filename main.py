import yaml
import pandas as pd
import csv
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_brand_bible():

def load_brand_bible():
    with open('brand_bible.yaml', 'r') as f:
        return yaml.safe_load(f)

def load_product_catalog():
    return pd.read_csv('product_catalog.csv')

def generate_visual_prompt(pillar, bible):
    visuals = bible['brand_bible']['visual_identity']
    base = f"Face: {visuals['face_reference']}. Hair: {visuals['hair']}. Style: {visuals['style']}. Lighting: {visuals['lighting']}."

    clothing = visuals['clothing_preferences'].get(pillar, "Neutral tones, elegant minimalist clothing")
    return f"{base} Clothing: {clothing}."

def associate_product(pillar, catalog):
    if pillar in ['fashion', 'beauty']:
        relevant_products = catalog[catalog['category'] == pillar]
        if not relevant_products.empty:
            return random.choice(relevant_products['product_id'].values)
    return ""

def process_calendar():
    bible = load_brand_bible()
    catalog = load_product_catalog()
    df = pd.read_csv('content_calendar.csv')

    for index, row in df.iterrows():
        # 1. Generate Visual Prompt
        df.at[index, 'visual_prompt'] = generate_visual_prompt(row['pillar'], bible)

        # 2. Associate Product
        df.at[index, 'product_id'] = associate_product(row['pillar'], catalog)

    df.to_csv('content_calendar.csv', index=False)
    print("Content calendar updated with visual prompts and product associations.")

if __name__ == "__main__":
    process_calendar()

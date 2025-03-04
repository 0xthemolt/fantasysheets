import psycopg2
import os
import requests
from pathlib import Path
import concurrent.futures

HERO_QUERY = """
    select distinct hero_id from flatten.heroes_current where is_deleted = 0
"""

def get_hero_ids():
    try:
        with psycopg2.connect(
            # "postgresql://postgres:$&roct8&rgp4NE@db.hhcuqhvmzwmehdsaamhn.supabase.co:5432/postgres"
            "postgresql://postgres.hhcuqhvmzwmehdsaamhn:$&roct8&rgp4NE@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
        ) as conn, conn.cursor() as cur:
            cur.execute(HERO_QUERY)
            hero_ids = [row[0] for row in cur.fetchall()]
            return hero_ids
    except Exception as e:
        print(f"Error fetching hero IDs: {e}")
        return []

def get_image_url(hero_id, stars, rarity):
    return f"https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v2/{rarity.lower()}/{hero_id}_{stars}.png"

def download_hero_image(hero_id, stars, rarity):
    # Create directory if it doesn't exist
    rarity_dir = Path(f"cards/{rarity.lower()}")
    rarity_dir.mkdir(parents=True, exist_ok=True)
    
    # Define file path
    file_path = rarity_dir / f"{hero_id}_{stars}.png"
    
    # Construct image URL
    image_url = get_image_url(hero_id, stars, rarity)
    
    try:
        # Download the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Save the image
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded hero {hero_id}, {rarity}, {stars} stars to {file_path}")
        return True
    except Exception as e:
        print(f"Error downloading image for hero {hero_id}, {rarity}, {stars} stars: {e}")
        return False

def download_all_hero_images():
    hero_ids = get_hero_ids()
    print(f"Found {len(hero_ids)} heroes")
    
    rarities = ["legendary", "epic", "rare", "common"]
    stars_range = range(1, 9)  # 1 to 8 stars
    
    # Create a list of all download tasks
    download_tasks = []
    for hero_id in hero_ids:
        for rarity in rarities:
            for stars in stars_range:
                download_tasks.append((hero_id, stars, rarity))
    
    total_images = len(download_tasks)
    success_count = 0
    
    print(f"Attempting to download {total_images} images with 4 concurrent workers")
    
    # Use ThreadPoolExecutor to run downloads concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks to the executor
        future_to_task = {
            executor.submit(download_hero_image, hero_id, stars, rarity): (hero_id, stars, rarity)
            for hero_id, stars, rarity in download_tasks
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_task):
            hero_id, stars, rarity = future_to_task[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
            except Exception as e:
                print(f"Task for hero {hero_id}, {rarity}, {stars} stars generated an exception: {e}")
    
    print(f"Downloaded {success_count} out of {total_images} hero images")

# Example usage:
download_all_hero_images()


import psycopg2
import json
import os
from datetime import datetime
import pandas as pd

# Load configuration from config.json
with open('C:/fantasy_top_analysis/pages/config.json', 'r') as config_file:
    config = json.load(config_file)

def get_db_connection():
    return psycopg2.connect(
        dbname="0xthemolt",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

# PLACEHOLDER_IMAGE = config['placeholder_image']    "placeholder_image": "https://pbs.twimg.com/profile_images/1754590022664101888/geh_HFDq_400x400.jpg",
TOURNAMENT_NUMBER = config['tournament_number']

query = f"""
with top50_heroes as (
    select 
        t.tournament_unique_key,
        t.tournament_league_unique_key,
        t.hero_handle,
        t.card_picture_url,
        t.hero_fantasy_score,
        count(*) as hero_count,
        COUNT(distinct tournament_player_deck_id) as deck_count,
        round(count(*)::decimal / COUNT(distinct tournament_player_deck_id) * 100, 2) as usage_percentage
    from agg.tournamentownership t 
    where player_rank <= 50
    and t.tournament_unique_key = 'Main {TOURNAMENT_NUMBER}'
    group by 1,2,3,4,5
    order by usage_percentage desc
)
,itm_heroes as (
    select 
        t.tournament_unique_key,
        t.tournament_league_unique_key,
        t.hero_handle,
        t.card_picture_url,
        t.hero_fantasy_score,
        count(*) as hero_count,
        COUNT(distinct tournament_player_deck_id) as deck_count,
        round(count(*)::decimal / COUNT(distinct tournament_player_deck_id) * 100, 2) as usage_percentage
    from agg.tournamentownership t 
    join flatten.GET_TOURNAMENT_BY_ID rewards
        on t.tournament_id = rewards.tournament_id 
        and t.player_rank between rewards.range_start and rewards.range_end 
        and rewards.reward_type = 'ETH'
    where t.tournament_unique_key = 'Main {TOURNAMENT_NUMBER}'
    group by 1,2,3,4,5
    order by usage_percentage desc
)
select * from (
    select *, 'top50' as category from top50_heroes
    union all
    select *, 'itm' as category from itm_heroes
) combined
order by tournament_unique_key, tournament_league_unique_key, category, usage_percentage desc
"""

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(query)
result = cursor.fetchall()
print(f"Number of records returned: {len(result)}")
conn.close()


# Convert results to nested dictionary format
hero_data = {
    "timestamp": datetime.now().isoformat(),
    "tournaments": {}
}

for row in result:
    tournament_key = row[0]
    league_key = row[1]
    category = row[8]  # new column for category (top50 or itm)
    hero_info = {
        "hero": row[2],
        "image_url": row[3],
        "fantasy_score": float(row[4]),
        "hero_count": int(row[5]),
        "deck_count": int(row[6]),
        "usage_percentage": float(row[7])
    }
    
    # Create nested structure
    if tournament_key not in hero_data["tournaments"]:
        hero_data["tournaments"][tournament_key] = {}
    
    if league_key not in hero_data["tournaments"][tournament_key]:
        hero_data["tournaments"][tournament_key][league_key] = {
            "top50": [],
            "itm": []
        }
    
    # Add to appropriate category if less than 10 heroes
    if len(hero_data["tournaments"][tournament_key][league_key][category]) < 10:
        hero_data["tournaments"][tournament_key][league_key][category].append(hero_info)

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)
# Save to JSON file
with open(os.path.join(output_dir, 'top_hero_utilization.json'), 'w') as f:
    json.dump(hero_data, f, indent=4)

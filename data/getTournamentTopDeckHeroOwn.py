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
with deck_counts as (
    select tournament_id, count(*) deck_count 
    from flatten.get_tournament_past_players gtpp 
    where tournament_unique_key =  'Main {TOURNAMENT_NUMBER}'
    group by 1
),
top_performers as (
    select tournament_unique_key,
        tournament_league_unique_key,
        hero_handle,
        hero_fantasy_score,
        count(*) as hero_count,
    from agg.tournamentownership t 
    join deck_counts decks on t.tournament_id = decks.tournament_id
    where (player_rank::float / deck_count * 100) <= 5  -- top 5% filter
    group by 1,2,3,4
)
select 
    tournament_unique_key,
    tournament_league_unique_key,
    hero_handle,
    hero_count,
    hero_fantasy_score,
    round((hero_count::float / (
        select sum(hero_count) 
        from top_performers t2 
        where t2.tournament_unique_key = t1.tournament_unique_key 
        and t2.tournament_league_unique_key = t1.tournament_league_unique_key
    ) * 100)::numeric, 2) as usage_percentage
from top_performers t1
order by tournament_unique_key, tournament_league_unique_key, hero_count desc
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
    hero_info = {
        "hero": row[2],
        "count": row[3],
        "fantasy_score": float(row[4]),
        "usage_percentage": float(row[5])
    }
    
    # Create nested structure
    if tournament_key not in hero_data["tournaments"]:
        hero_data["tournaments"][tournament_key] = {}
    
    if league_key not in hero_data["tournaments"][tournament_key]:
        hero_data["tournaments"][tournament_key][league_key] = []
    
    # Only append if we haven't reached 10 heroes for this tournament/league combination
    if len(hero_data["tournaments"][tournament_key][league_key]) < 10:
        hero_data["tournaments"][tournament_key][league_key].append(hero_info)

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)
# Save to JSON file
with open(os.path.join(output_dir, 'top_hero_utilization.json'), 'w') as f:
    json.dump(hero_data, f, indent=4)

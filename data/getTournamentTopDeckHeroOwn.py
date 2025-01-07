import psycopg2
import json
import os
from datetime import datetime
import pandas as pd

def get_db_connection():
    return psycopg2.connect(
        dbname="0xthemolt",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )


query = """
with deck_counts as (
    select tournament_id, count(*) deck_count 
    from flatten.get_tournament_past_players gtpp 
    group by 1
),
top_performers as (
    select tournament_league_unique_key,hero_handle,hero_fantasy_score,
        count(*) as hero_count
    from agg.tournamentownership t 
    join deck_counts decks on t.tournament_id = decks.tournament_id
    where tournament_unique_key = 'Main 33'
    and (player_rank::float / deck_count * 100) <= 5  -- top 5% filter
    group by 1,2,3
    order by hero_count desc
    limit 10
)
select 
    hero_handle,
    hero_count,
    hero_fantasy_score,
    round((hero_count::float / (select sum(hero_count) from top_performers) * 100)::numeric, 2) as usage_percentage
from top_performers
order by hero_count desc
"""

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(query)
result = cursor.fetchall()
conn.close()

# Convert results to dictionary format
hero_data = {
    "timestamp": datetime.now().isoformat(),
    "tournament": "Bronze Main 33",
    "top_heroes": [
        {
            "hero": row[0],
            "count": row[1],
            "fantasy_score": float(row[2]),
            "usage_percentage": float(row[3])
        } for row in result
    ]
}


# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)
# Save to JSON file
with open(os.path.join(output_dir, 'top_hero_utilization.json'), 'w') as f:
    json.dump(hero_data, f, indent=4)

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
with base_records as (
    select 
    	tournament_id,
        tournament_unique_key,
        tournament_league_unique_key,
        hero_handle,
        card_picture_url,
        hero_fantasy_score,
        tournament_player_deck_id,
        player_rank
    from agg.tournamentownership t 
    where t.tournament_unique_key = 'Main 33'
    --and tournament_league_unique_key = 'Gold Main 33'
),
top50_records as (
    select *
    from base_records
    where player_rank <= 50
),
itm_records as (
    select br.*
    from base_records br
    join flatten.GET_TOURNAMENT_BY_ID rewards
	   on br.tournament_id = rewards.tournament_id 
	    and br.player_rank between rewards.range_start and rewards.range_end 
	    and rewards.reward_type = 'ETH'
),
deck_counts as (
    select tournament_id,'top50' as category, count(distinct tournament_player_deck_id) as total_decks
    from top50_records
    group by 1
    union all
    select tournament_id,'itm' as category, count(distinct tournament_player_deck_id) as total_decks
    from itm_records
    group by 1
),
hero_stats as (
    select 
    	t.tournament_id,
        t.tournament_unique_key,
        t.tournament_league_unique_key,
        t.hero_handle,
        t.card_picture_url,
        t.hero_fantasy_score,
        count(*) as hero_count,
        'top50' as category
    from top50_records t
    group by 1,2,3,4,5,6
    union all
    select 
    	t.tournament_id,
        t.tournament_unique_key,
        t.tournament_league_unique_key,
        t.hero_handle,
        t.card_picture_url,
        t.hero_fantasy_score,
        count(*) as hero_count,
        'itm' as category
    from itm_records t
    group by 1,2,3,4,5,6
)
,base as (
select 
    h.*,
    d.total_decks,
    round(h.hero_count::decimal / d.total_decks * 100, 2) as usage_percentage,
    row_number() over (partition by h.tournament_id, h.category order by round(h.hero_count::decimal / d.total_decks * 100, 2) desc) as rnk
from hero_stats h
join deck_counts d on h.category = d.category and h.tournament_id = d.tournament_id
)
select tournament_unique_key,tournament_league_unique_key,hero_handle,card_picture_url,hero_fantasy_score as fantasy_score,hero_count,category,usage_percentage,rnk
from base
where rnk <= 10
order by tournament_id,category,rnk asc
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
    tournament_id = row[0]  # tournament_unique_key
    league_key = row[1]     # tournament_league_unique_key
    hero_info = {
        "hero": row[2],     # hero_handle
        "image_url": row[3], # card_picture_url
        "fantasy_score": float(row[4]),  # hero_fantasy_score
        "hero_count": int(row[5]),       # hero_count
        "usage_percentage": float(row[7]) # usage_percentage
    }
    
    category = row[6]  # category
    
    # Create nested structure
    if tournament_id not in hero_data["tournaments"]:
        hero_data["tournaments"][tournament_id] = {
            "tournament_key": tournament_id,  # Using tournament_unique_key directly
            "leagues": {}
        }
    
    if league_key not in hero_data["tournaments"][tournament_id]["leagues"]:
        hero_data["tournaments"][tournament_id]["leagues"][league_key] = {
            "top50": [],
            "itm": []
        }
    
    # Add to appropriate category
    hero_data["tournaments"][tournament_id]["leagues"][league_key][category].append(hero_info)

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)
# Save to JSON file
with open(os.path.join(output_dir, 'league_winners.json'), 'w') as f:
    json.dump(hero_data, f, indent=4)

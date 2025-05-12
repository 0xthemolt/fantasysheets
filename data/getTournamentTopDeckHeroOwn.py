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
    	t.tournament_id,
        t.tournament_unique_key,
        t2.league,
        t.hero_handle,
        t.hero_id,
        ghwst.fantasy_score,
        t.tournament_player_deck_id,
        t.unique_player_rank as player_rank,
        card_stars.hero_stars,
        coalesce(
        	(case 
        	      when t2.league = 'Reverse'  then
        	      	case when t.player_score = 0 then gtbi.reward / 5
        	 	    else  
        	 	    (1 - (t.hero_score::decimal / NULLIF(player_score, 0)::decimal)) / 
         				SUM(1 - (t.hero_score::decimal / NULLIF(player_score, 0)::decimal)) OVER(partition by tournament_player_deck_id) * gtbi.reward
        	 	    end
        	 	  when t2.league <>  'Reverse'  then
        	 	  	case when t.hero_score  = 0 then 0 
					else (t.hero_score::float / t.player_score) * gtbi.reward
					end
			end) ,0) as reward_value_added,
        t.db_updated_cst + INTERVAL '5 hours' as db_updated_utc
    from agg.tournamentownership t 
    join flatten.get_tournaments t2 
    	on t.tournament_id = t2.tournament_id
    left join flatten.get_heros_with_stats_tournament ghwst 
    	on t.hero_id = ghwst.hero_id
    	and t.tournament_unique_key = ghwst.tournament_unique_key
    left join flatten.get_cards_flags_stars card_stars
	    ON t.hero_id = card_stars.hero_id
	    and t2.start_timestamp between card_stars.start_datetime and card_stars.end_datetime
	left join flatten.get_tournament_by_id gtbi 
		on t.tournament_id = gtbi.tournament_id
		and t.player_rank between gtbi.range_start  and gtbi.range_end
		and gtbi.reward_type = 'ETH'
    where t.tournament_unique_key = 'Main 51'
)
,reward_value_added as (
select tournament_id,tournament_unique_key,league,hero_handle,hero_id,fantasy_score,hero_stars,'rva' as category,db_updated_utc,suM(reward_value_added) reward_value_added,row_number() over (partition by tournament_id order by suM(reward_value_added) desc) as rnk
from base_records
group by 1,2,3,4,5,6,7,8,9
order by 3 desc
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
--select * from itm_records where league = 'Silver' order by player_rank  asc;
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
        t.league,
        t.hero_handle,
        t.hero_id,
        t.fantasy_score,
        t.hero_stars,
        t.db_updated_utc,
        count(*) as hero_count,
        'top50' as category
    from top50_records t
    group by 1,2,3,4,5,6,7,8
    union all
    select 
    	t.tournament_id,
        t.tournament_unique_key,
        t.league,
        t.hero_handle,
        t.hero_id,
        t.fantasy_score,
        t.hero_stars,
        t.db_updated_utc,
        count(*) as hero_count,
        'itm' as category
    from itm_records t
    group by 1,2,3,4,5,6,7,8
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
select tournament_unique_key,league,hero_handle,concat('https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v2/argent/',hero_id,'_',hero_stars,'.png') as card_picture_url,fantasy_score ,hero_stars,hero_count,category,usage_percentage,0 as reward_value_added,rnk,db_updated_utc
from base
where rnk <= 10
union all
select tournament_unique_key,league,hero_handle,concat('https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v2/argent/',hero_id,'_',hero_stars,'.png') as card_picture_url,fantasy_score ,hero_stars,0 as hero_count,category,0 as usage_percentage,reward_value_added,rnk,db_updated_utc
from reward_value_added
where rnk <= 10
order by tournament_unique_key,category,rnk asc
"""

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(query)
result = cursor.fetchall()

print(f"Number of records returned: {len(result)}")
conn.close()


# Convert results to nested dictionary format
hero_data = {
    "metadata": {
        "data_freshness": result[0][11].isoformat() if result else None  # Get db_updated_utc from last column
    },
    "tournaments": {}
}

for row in result:
    tournament_id = row[0]  # tournament_unique_key
    league_key = row[1]     # league
    hero_info = {
        "hero": row[2],     # hero_handle
        "image_url": row[3], # card_picture_url
        "fantasy_score": float(row[4]),  # fantasy_score
        "hero_stars": row[5], # hero_stars
        "hero_count": int(row[6]),       # hero_count
        "usage_percentage": float(row[8]), # usage_percentage
        "reward_value_added": float(row[9]) # reward_value_added
    }
    
    category = row[7]  # category
    
    # Create nested structure
    if tournament_id not in hero_data["tournaments"]:
        hero_data["tournaments"][tournament_id] = {
            "tournament_key": tournament_id,  # Using tournament_unique_key directly
            "leagues": {}
        }
    
    if league_key not in hero_data["tournaments"][tournament_id]["leagues"]:
        hero_data["tournaments"][tournament_id]["leagues"][league_key] = {
            "top50": [],
            "itm": [],
            "rva": []
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

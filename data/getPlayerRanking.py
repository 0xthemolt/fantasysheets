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

# First query into league_decks_df
conn = get_db_connection()
cursor = conn.cursor()
player_ranking_query = f"""with tournaments as (
select  player_id
,count(distinct tournament_unique_key) mains_played
,couNT(*) as deck_count
--,sum(case when player_rank <= 10 then 1 else 0 end) as top_ten_finish_count
from flatten.get_tournament_past_players gtpp 
--where player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and tournament_unique_key = 'Main 32'
group by 1
)
,eth_won as (
select player_id--,tournament_unique_key
,suM(reward_eth) reward_eth
from flatten.get_tournament_histories_by_player_id 
--where player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and tournament_unique_key = 'Main 31'
group by 1--,2
having suM(reward_eth) <> 0
)
select players.player_id,players.player_handle ,players.player_name ,players.profile_picture 
,suM(eth_won.reward_eth)reward_eth
,suM(coalesce(players.portfolio_value,0)) as portfolio
,sum(players.fan_pts + referral_pts) fan_pts
,sum(players.gold) gold
,suM(players.stars) stars
,sum(tournaments.deck_count) as decks
,suM(players.number_of_cards) as cards
,max(updated) freshness_timestamp
from flatten.get_player_basic_data players
join eth_won
	on players.player_id = eth_won.player_id
join tournaments 
	on players.player_id  = tournaments.player_id
--where players.player_id = '0x162F95a9364c891028d255467F616902A479681a'
--	and t_hist.tournament_unique_key  = 'Main 32'
group by 1,2,3,4"""
player_ranking_df = pd.read_sql_query(player_ranking_query, conn)
cursor.close()

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'players')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)

# Convert timestamps to string format before JSON serialization
player_ranking_df['freshness_timestamp'] = player_ranking_df['freshness_timestamp'].astype(str)

# Get the maximum freshness timestamp
max_freshness = player_ranking_df['freshness_timestamp'].max()

# Remove freshness_timestamp from DataFrame before converting to dict
player_ranking_df = player_ranking_df.drop('freshness_timestamp', axis=1)

# Convert DataFrame to a list of dictionaries
player_ranking_data = player_ranking_df.to_dict(orient='records')

# Create the final JSON structure with metadata
final_json = {
    "metadata": {
        "last_updated": max_freshness,
        "record_count": len(player_ranking_data)
    },
    "players": player_ranking_data
}

# Write to JSON file using absolute path
output_file = os.path.join(output_dir, 'player_ranking.json')
with open(output_file, 'w') as f:
    json.dump(final_json, f, indent=4)

# Print the full path
print(f"Writing data to: {output_file}")

# Close the final connection
conn.close()



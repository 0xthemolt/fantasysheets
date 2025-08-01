import psycopg2
import json
import os
from datetime import datetime
import pandas as pd

def get_db_connection():
    return psycopg2.connect(
        dbname="postgres",
    user="postgres.hhcuqhvmzwmehdsaamhn",
    password="Wafj2DCrI6Yjbe4I",
    host="aws-0-us-west-1.pooler.supabase.com",
    port="5432"
    )



# First query into league_decks_df
conn = get_db_connection()
cursor = conn.cursor()
player_ranking_query = f"""with base as (
select t.tournament_unique_key ,t.league ,t.registered_decks,t.start_timestamp
,tplayers.player_id,gpbd.player_name,gpbd.profile_picture 
,tplayers.unique_player_rank as player_rank
,1 - (tplayers.unique_player_rank - 1) / (t.registered_decks) normalized_rank  --x min = total registered / worse place, x max = best (rank 1)
,coalesce(reward,0) eth_reward
,row_number() over (partition by t.tournament_league_unique_key,tplayers.player_id order by tplayers.unique_player_rank asc) as best_deck_rank
 FROM flatten.tournament_players tplayers
 join flatten.GET_TOURNAMENTS t  
	on tplayers.tournament_id  = t.tournament_id 
left join  flatten.tournament_rewards rewards_eth
	on tplayers.tournament_id = rewards_eth.tournament_id
	and tplayers.unique_player_rank between  rewards_eth.range_start and rewards_eth.range_end
	and rewards_eth.reward_type = 'ETH'
left join flatten.get_player_basic_data gpbd 
	on tplayers.player_id  = gpbd.player_id 
where 1=1
--tplayers.player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and t.tournament_unique_key  = 'Main 31'
and t.start_timestamp >= '2024-07-01'
)
,qualified_players as (
select player_id,COUNT(DISTINCT tournament_unique_key) mains_played,sum(case when best_deck_rank = 1 then eth_reward else 0 end) qualified_player_eth_won
from base
where start_timestamp >= NOW() at TIME zone 'UTC' - interval '1 month'
group by 1
having count(*) >= 2
and SUM(case when best_deck_rank = 1 then eth_reward else 0 end) > 0.05
)
select start_timestamp,tournament_unique_key ,league,base.player_id,player_name,profile_picture,count(*) as total_decks
,max(case when best_deck_rank = 1 then player_rank else 0 end) as best_deck_rank
,sum(eth_reward) total_eth_won
,max(case when best_deck_rank = 1 then normalized_rank else 0 end) as best_deck_norm_rank
from base
join qualified_players qp on base.player_id = qp.player_id
group by 1,2,3,4,5,6
order by start_timestamp asc"""
player_ranking_df = pd.read_sql_query(player_ranking_query, conn)
cursor.close()

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)

# Convert timestamps to string format before JSON serialization
player_ranking_df['start_timestamp'] = player_ranking_df['start_timestamp'].astype(str)

# Convert DataFrame to a list of dictionaries
player_ranking_data = player_ranking_df.to_dict(orient='records')

# Write to JSON file using absolute path
output_file = os.path.join(output_dir, 'player_ranking.json')
with open(output_file, 'w') as f:
    json.dump(player_ranking_data, f, indent=4)

# Print the full path
print(f"Writing data to: {output_file}")

# Close the final connection
conn.close()



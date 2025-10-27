import psycopg2
import json
import os
from datetime import datetime
import pandas as pd

def get_db_connection():
    return psycopg2.connect(
dbname="postgres",
        # user="postgres.hhcuqhvmzwmehdsaamhn",
        user="postgres",
        password="Wafj2DCrI6Yjbe4I",
        # host="aws-0-us-west-1.pooler.supabase.com",
        host="db.hhcuqhvmzwmehdsaamhn.supabase.co",
        port="5432"
    )

# First, get all unique seasons
conn = get_db_connection()
cursor = conn.cursor()

seasons_query = """
SELECT season, min(vs.season_start_date), max(vs.season_end_date)
FROM flatten.vwtournament_seasons vs 
WHERE season <> 0
GROUP BY 1
ORDER BY 1 ASC
"""

seasons_df = pd.read_sql_query(seasons_query, conn)
cursor.close()
conn.close()

print(f"Found {len(seasons_df)} seasons to process:")
print(seasons_df)

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'players')

# Ensure the players directory exists
os.makedirs(output_dir, exist_ok=True)

# Process each season
for _, season_row in seasons_df.iterrows():
    season = int(season_row['season'])  # Convert to int first
    print(f"\nProcessing season {season}...")
    
    # Connect to database for this season
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Updated player ranking query with season parameter
    player_ranking_query = f"""set statement_timeout = '5min';
with finished_tournaments as (
select vs.season,tournament_id,tournament_unique_key,tournament_league_unique_key,league,t.tournament_number,start_timestamp,end_timestamp,registered_decks 
,DENSE_RANK() over (order by t.tournament_number desc) as finished_tournament_seq_nbr
from  flatten.get_tournaments t
join flatten.vwtournament_seasons vs 
	on t.tournament_number = vs.tournament_number 
where start_timestamp >= '2024-07-01'
and tournament_status = 'finished'
and season = {season}
)
,player_deck_counts as (
select  player_id
,count(distinct t.tournament_unique_key) mains_played
,couNT(*) as deck_count
--,sum(case when player_rank <= 10 then 1 else 0 end) as top_ten_finish_count
from flatten.TOURNAMENT_PLAYERS gtpp 
join finished_tournaments t
	on gtpp.tournament_id = t.tournament_id
group by 1
)
,rewards_won_criteria as (
select ph.player_id
from flatten.tournament_player_history  ph
join finished_tournaments t
   on ph.tournament_id::text = t.tournament_id::text
group by 1
)
,eth_frags_won as (
select ph.player_id
,suM(reward_fan) reward_fan
,suM(reward_eth) reward_eth
,sum(reward_fragment) + sum(reward_pack * 100) reward_frag 
from flatten.tournament_player_history  ph
join finished_tournaments t
   on ph.tournament_id::text = t.tournament_id::text
join rewards_won_criteria r
   on ph.player_id = r.player_id
group by 1
)
,touranment_rankings as (
select t.tournament_unique_key ,t.league ,t.registered_decks,t.start_timestamp,t.finished_tournament_seq_nbr
,tplayers.player_id,gpbd.player_name,gpbd.profile_picture 
,tplayers.player_rank
,1 - (tplayers.player_rank - 1) / (t.registered_decks) normalized_rank  --x min = total registered / worse place, x max = best (rank 1)
,coalesce(reward,0) eth_reward
,row_number() over (partition by t.tournament_league_unique_key,tplayers.player_id order by tplayers.player_rank asc) as best_deck_rank
 FROM flatten.TOURNAMENT_PLAYERS tplayers
 join finished_tournaments t
	on tplayers.tournament_id  = t.tournament_id 
left join  flatten.TOURNAMENT_REWARDS rewards_eth
	on tplayers.tournament_id = rewards_eth.tournament_id
	and tplayers.player_rank between  rewards_eth.range_start and rewards_eth.range_end
	and rewards_eth.reward_type = 'ETH'
left join flatten.get_player_basic_data gpbd 
	on tplayers.player_id  = gpbd.player_id 
join eth_frags_won 
    on tplayers.player_id = eth_frags_won.player_id
where 1=1
)  
,league_ranking as (
select league,player_id
,avg(normalized_rank) as avg_best_deck_norm_score
,case when avg(normalized_rank) is null then null else dense_rank() over (partition by league order by avg(normalized_rank)  desc) end as avg_best_deck_norm_rank
from touranment_rankings
where best_deck_rank = 1
--and league = 'Silver'
group by 1,2
having count(*) >= 2 --at least 2 tournaments
)
,league_ranking_l5 as (
select league,player_id
,avg(normalized_rank) as avg_best_deck_norm_score
,case when avg(normalized_rank) is null then null else dense_rank() over (partition by league order by avg(normalized_rank)  desc) end as avg_best_deck_norm_rank
,min(tournament_unique_key)mint,max(tournament_unique_key)maxt
from touranment_rankings
where best_deck_rank = 1
and finished_tournament_seq_nbr <= 5
group by 1,2
having count(*) >= 2 --at least 2 tournaments
)
select players.player_id,players.player_handle ,players.player_name ,players.profile_picture 
,case when first_tournament.tournament_unique_key= 'Flash Tournament' then 'Flash'
when first_tournament.tournament_unique_key= 'Common Only ✳️ Capped 20 🌟 ' then 'Common Capped 20'
when first_tournament.tournament_unique_key= 'Common Only ✳️ Capped 15 🌟' then 'Common Capped 15'
when first_tournament.tournament_unique_key= 'Rare Only 💠' then 'Rare Only'
else first_tournament.tournament_unique_key  end as first_tournament
,null as hours_since_last_activity
,suM(eth_frags_won.reward_eth) reward_eth
,suM(eth_frags_won.reward_frag) reward_frag
,suM(coalesce(players.portfolio_value,0)) as portfolio
,sum(eth_frags_won.reward_fan) fan_pts
,sum(players.gold) blast_gold
,suM(players.stars) stars
,sum(player_deck_counts.deck_count) as decks
,suM(players.number_of_cards) as cards
,max(touranment_rankings_diamond.avg_best_deck_norm_rank) as diamond_norm_rank
,max(touranment_rankings_diamond_l5.avg_best_deck_norm_rank) as diamond_norm_rank_l5
,max(touranment_rankings_plat.avg_best_deck_norm_rank) as platinum_norm_rank
,max(touranment_rankings_plat_l5.avg_best_deck_norm_rank) as platinum_norm_rank_l5
,max(touranment_rankings_gold.avg_best_deck_norm_rank) as gold_norm_rank
,max(touranment_rankings_gold_l5.avg_best_deck_norm_rank) as gold_norm_rank_l5
,max(touranment_rankings_silver.avg_best_deck_norm_rank) as silver_norm_rank
,max(touranment_rankings_silver_l5.avg_best_deck_norm_rank) as silver_norm_rank_l5
,max(touranment_rankings_bronze.avg_best_deck_norm_rank) as bronze_norm_rank
,max(touranment_rankings_bronze_l5.avg_best_deck_norm_rank) as bronze_norm_rank_l5
,max(touranment_rankings_reverse.avg_best_deck_norm_rank) as reverse_norm_rank
,max(touranment_rankings_reverse_l5.avg_best_deck_norm_rank) as reverse_norm_rank_l5
,max(null) as buy_vol
,max(null) as pack_vol
,max(null) as sell_vol
,max(null) as net_vol
,max(null) as trade_count
,max(null) as max_buy
,max(null) as max_sell
,max(updated) freshness_timestamp
,max(case when hc.hero_handle is null then 0 else 1 end) is_hero
from flatten.get_player_basic_data players
left join flatten.heroes_current hc 
    on players.player_handle  = hc.hero_handle
join flatten.GET_TOURNAMENTS first_tournament
	on players.first_tournament = first_tournament.tournament_id
join flatten.GET_TOURNAMENTS last_tournament
	on players.last_tournament = last_tournament.tournament_id
join eth_frags_won  
	on players.player_id = eth_frags_won.player_id
join player_deck_counts 
	on players.player_id  = player_deck_counts.player_id
left join league_ranking touranment_rankings_diamond
    on players.player_id = touranment_rankings_diamond.player_id
    and touranment_rankings_diamond.league = 'Diamond'
left join league_ranking touranment_rankings_plat
    on players.player_id = touranment_rankings_plat.player_id
    and touranment_rankings_plat.league = 'Platinum'
left join league_ranking touranment_rankings_gold
    on players.player_id = touranment_rankings_gold.player_id
    and touranment_rankings_gold.league = 'Gold'
left join league_ranking touranment_rankings_silver
    on players.player_id = touranment_rankings_silver.player_id
    and touranment_rankings_silver.league = 'Silver'
left join league_ranking touranment_rankings_bronze
    on players.player_id = touranment_rankings_bronze.player_id
    and touranment_rankings_bronze.league = 'Bronze'
left join league_ranking touranment_rankings_reverse
    on players.player_id = touranment_rankings_reverse.player_id
    and touranment_rankings_reverse.league = 'Reverse'
left join league_ranking_l5 touranment_rankings_diamond_l5
    on players.player_id = touranment_rankings_diamond_l5.player_id
    and touranment_rankings_diamond_l5.league = 'Diamond'
left join league_ranking_l5 touranment_rankings_plat_l5
    on players.player_id = touranment_rankings_plat_l5.player_id
    and touranment_rankings_plat_l5.league = 'Platinum'
left join league_ranking_l5 touranment_rankings_gold_l5
    on players.player_id = touranment_rankings_gold_l5.player_id
    and touranment_rankings_gold_l5.league = 'Gold'
left join league_ranking_l5 touranment_rankings_silver_l5
    on players.player_id = touranment_rankings_silver_l5.player_id
    and touranment_rankings_silver_l5.league = 'Silver'
left join league_ranking_l5 touranment_rankings_bronze_l5
    on players.player_id = touranment_rankings_bronze_l5.player_id
    and touranment_rankings_bronze_l5.league = 'Bronze'
left join league_ranking_l5 touranment_rankings_reverse_l5
    on players.player_id = touranment_rankings_reverse_l5.player_id
    and touranment_rankings_reverse_l5.league = 'Reverse'
--where players.player_id = '0x162F95a9364c891028d255467F616902A479681a'
--	and t_hist.tournament_unique_key  = 'Main 32'
group by 1,2,3,4,5
order by sum(eth_frags_won.reward_fan)  desc
limit 500"""

    try:
        player_ranking_df = pd.read_sql_query(player_ranking_query, conn)
        
        if len(player_ranking_df) == 0:
            print(f"No data found for season {season}, skipping...")
            cursor.close()
            conn.close()
            continue
        
        # Convert timestamps to string format before JSON serialization
        player_ranking_df['freshness_timestamp'] = player_ranking_df['freshness_timestamp'].astype(str)

        # Handle NaN values in norm rank columns
        rank_columns = ['diamond_norm_rank', 'platinum_norm_rank','gold_norm_rank', 'silver_norm_rank', 'bronze_norm_rank', 'reverse_norm_rank','diamond_norm_rank_l5','platinum_norm_rank_l5','gold_norm_rank_l5','silver_norm_rank_l5','bronze_norm_rank_l5','reverse_norm_rank_l5']
        for col in rank_columns:
            player_ranking_df[col] = player_ranking_df[col].fillna(0).astype(float)

        # Get the maximum freshness timestamp
        max_freshness = player_ranking_df['freshness_timestamp'].max()

        # Remove freshness_timestamp from DataFrame before converting to dict
        player_ranking_df = player_ranking_df.drop('freshness_timestamp', axis=1)

        # Convert DataFrame to a list of dictionaries
        player_ranking_data = player_ranking_df.to_dict(orient='records')

        # Create the final JSON structure with metadata
        final_json = {
            "metadata": {
                "season": season,  # Already an int now
                "last_updated": max_freshness,
                "record_count": len(player_ranking_data)
            },
            "players": player_ranking_data
        }

        # Write to JSON file using season-specific filename
        output_file = os.path.join(output_dir, f'player_ranking_season_{season}.json')
        with open(output_file, 'w') as f:
            json.dump(final_json, f, indent=4)

        print(f"Successfully wrote {len(player_ranking_data)} records to: {output_file}")
        
    except Exception as e:
        print(f"Error processing season {season}: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()

print(f"\nCompleted processing all seasons. Files saved to: {output_dir}")



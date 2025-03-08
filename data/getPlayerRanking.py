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
,count(distinct gtpp.tournament_unique_key) mains_played
,couNT(*) as deck_count
--,sum(case when player_rank <= 10 then 1 else 0 end) as top_ten_finish_count
from flatten.get_tournament_past_players gtpp 
join flatten.get_tournaments t
	on gtpp.tournament_id = t.tournament_id
--where player_id = '0x162F95a9364c891028d255467F616902A479681a'
and t.start_timestamp >= '2024-07-01'
and t.tournament_status = 'finished'
group by 1
)
,eth_frags_won as (
select player_id
--,tournament_unique_key
,suM(reward_eth) reward_eth
,sum(reward_frag) + sum(reward_pack * 100) reward_frag 
from flatten.get_tournament_histories_by_player_id 
--where player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and tournament_unique_key = 'Main 31'
group by 1--,2
having suM(reward_eth) <> 0
)
,touranment_rankings as (
select t.tournament_unique_key ,t.league ,t.registered_decks,t.start_timestamp,t.tournament_seq_nbr
,tplayers.player_id,gpbd.player_name,gpbd.profile_picture 
,tplayers.player_rank
,1 - (tplayers.player_rank - 1) / (t.registered_decks) normalized_rank  --x min = total registered / worse place, x max = best (rank 1)
,coalesce(reward,0) eth_reward
,row_number() over (partition by t.tournament_league_unique_key,tplayers.player_id order by tplayers.player_rank asc) as best_deck_rank
 FROM flatten.GET_TOURNAMENT_PAST_PLAYERS tplayers
 join flatten.GET_TOURNAMENTS t
	on tplayers.tournament_id  = t.tournament_id 
left join  flatten.GET_TOURNAMENT_BY_ID rewards_eth
	on tplayers.tournament_id = rewards_eth.tournament_id
	and tplayers.player_rank between  rewards_eth.range_start and rewards_eth.range_end
	and rewards_eth.reward_type = 'ETH'
left join flatten.get_player_basic_data gpbd 
	on tplayers.player_id  = gpbd.player_id 
join eth_frags_won 
    on tplayers.player_id = eth_frags_won.player_id
where 1=1
--and tplayers.player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and t.tournament_unique_key  = 'Main 31'
and t.tournament_status = 'finished'
and t.start_timestamp >= '2024-07-01'
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
from touranment_rankings
where best_deck_rank = 1
and tournament_seq_nbr <= 5
group by 1,2
having count(*) >= 2 --at least 2 tournaments
)
, trade_volume as (
    SELECT 
        buyer_id as player_id,
        DATE(timestamp) as trade_date,
        sum(price) as buy_volume,
        sum(0) as sell_volume,
        count(*) as trade_count,
        max(price) as max_buy,
        0 as max_sell
    FROM flatten.get_hero_last_trades ghlt 
    where buyer_id <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
    and seller_id <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
    GROUP BY 1,2
    UNION
    SELECT 
        seller_id as player_id,
        DATE(timestamp) as trade_date,
        sum(0) as buy_volume,
        sum(price) as sell_volume,
        count(*) as trade_count,
        0 as max_buy,
        max(price) as max_sell
    FROM flatten.get_hero_last_trades ghlt 
    where buyer_id <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
    and seller_id <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
    GROUP BY 1,2
),
consecutive_days as (
    SELECT 
        player_id,
        trade_date,
        trade_date - INTERVAL '1 day' * ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY trade_date) as grp
    FROM (SELECT DISTINCT player_id, trade_date FROM trade_volume)
),
streak_lengths as (
    SELECT 
        player_id,
        COUNT(*) as streak_length,
        MIN(trade_date) as streak_start,
        MAX(trade_date) as streak_end
    FROM consecutive_days
    GROUP BY player_id, grp
)
,trade_volume_by_player as (
    SELECT  
        tv.player_id,
        sum(buy_volume) as buy_volume,
        sum(sell_volume) as sell_volume,
        sum(trade_count) as trade_count,
        max(max_buy) as max_buy,
        max(max_sell) as max_sell,
        MAX(sl.streak_length) as longest_trading_streak
    FROM trade_volume tv
    LEFT JOIN (
        SELECT player_id, MAX(streak_length) as streak_length
        FROM streak_lengths
        GROUP BY player_id
    ) sl ON tv.player_id = sl.player_id
    GROUP BY 1
)
select players.player_id,players.player_handle ,players.player_name ,players.profile_picture 
,case when first_tournament.tournament_unique_key= 'Flash Tournament' then 'Flash'
when first_tournament.tournament_unique_key= 'Common Only ✳️ Capped 20 🌟 ' then 'Common Capped 20'
when first_tournament.tournament_unique_key= 'Common Only ✳️ Capped 15 🌟' then 'Common Capped 15'
when first_tournament.tournament_unique_key= 'Rare Only 💠' then 'Rare Only'
else first_tournament.tournament_unique_key  end as first_tournament
,EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' - MAX(greatest(last_tournament.start_timestamp,players.last_trade_timestamp)))) / 3600 as hours_since_last_activity
,suM(eth_frags_won.reward_eth) reward_eth
,suM(eth_frags_won.reward_frag) reward_frag
,suM(coalesce(players.portfolio_value,0)) as portfolio
,sum(players.fan_pts + referral_pts) fan_pts
,sum(players.gold) blast_gold
,suM(players.stars) stars
,min(elo.overall_elo_rank) as elo_rank
,max(elo.elo_score) as elo_score
,max(elo.elo_image) as elo_image
,sum(tournaments.deck_count) as decks
,suM(players.number_of_cards) as cards
,max(touranment_rankings_elite.avg_best_deck_norm_rank) as elite_norm_rank
,max(touranment_rankings_elite_l5.avg_best_deck_norm_rank) as elite_norm_rank_l5
,max(touranment_rankings_gold.avg_best_deck_norm_rank) as gold_norm_rank
,max(touranment_rankings_gold_l5.avg_best_deck_norm_rank) as gold_norm_rank_l5
,max(touranment_rankings_silver.avg_best_deck_norm_rank) as silver_norm_rank
,max(touranment_rankings_silver_l5.avg_best_deck_norm_rank) as silver_norm_rank_l5
,max(touranment_rankings_bronze.avg_best_deck_norm_rank) as bronze_norm_rank
,max(touranment_rankings_bronze_l5.avg_best_deck_norm_rank) as bronze_norm_rank_l5
,max(touranment_rankings_reverse.avg_best_deck_norm_rank) as reverse_norm_rank
,max(touranment_rankings_reverse_l5.avg_best_deck_norm_rank) as reverse_norm_rank_l5
,max(coalesce(tvbp.buy_volume,0)) as buy_vol
,max(coalesce(tvbp.buy_volume,0) - coalesce(tvbp.sell_volume,0)) as net_vol
,max(coalesce(tvbp.trade_count,0)) as trade_count
,max(coalesce(tvbp.max_buy,0)) as max_buy
,max(coalesce(tvbp.max_sell,0)) as max_sell
,max(coalesce(tvbp.longest_trading_streak,0)) as longest_trade_streak
,max(updated) freshness_timestamp
from flatten.get_player_basic_data players
left join flatten.elo_leaderboard elo
	on players.player_id = elo.player_id
join flatten.GET_TOURNAMENTS first_tournament
	on players.first_tournament = first_tournament.tournament_id
join flatten.GET_TOURNAMENTS last_tournament
	on players.last_tournament = last_tournament.tournament_id
join eth_frags_won  
	on players.player_id = eth_frags_won.player_id
join tournaments 
	on players.player_id  = tournaments.player_id
left join trade_volume_by_player tvbp
	on players.player_id = tvbp.player_id
left join league_ranking touranment_rankings_elite
    on players.player_id = touranment_rankings_elite.player_id
    and touranment_rankings_elite.league = 'Elite'
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
left join league_ranking_l5 touranment_rankings_elite_l5
    on players.player_id = touranment_rankings_elite_l5.player_id
    and touranment_rankings_elite_l5.league = 'Elite'
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
order by sum(players.fan_pts + referral_pts)  desc"""
player_ranking_df = pd.read_sql_query(player_ranking_query, conn)
cursor.close()

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'players')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)

# Convert timestamps to string format before JSON serialization
player_ranking_df['freshness_timestamp'] = player_ranking_df['freshness_timestamp'].astype(str)

# Handle NaN values in norm rank columns
rank_columns = ['elite_norm_rank', 'gold_norm_rank', 'silver_norm_rank', 'bronze_norm_rank', 'reverse_norm_rank','elite_norm_rank_l5','gold_norm_rank_l5','silver_norm_rank_l5','bronze_norm_rank_l5','reverse_norm_rank_l5']
for col in rank_columns:
    player_ranking_df[col] = player_ranking_df[col].fillna(0).astype(float)

# Handle NaN values in norm rank columns
elo_columns = ['elo_score', 'elo_rank']
for col in elo_columns:
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



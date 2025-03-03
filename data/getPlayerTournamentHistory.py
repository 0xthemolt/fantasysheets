import psycopg2
import json
import os
from datetime import datetime

# Load configuration from config.json
with open('C:/fantasy_top_analysis/pages/config.json', 'r') as config_file:
    config = json.load(config_file)

TOURNAMENT_NUMBER = config['tournament_number']

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="0xthemolt",
    user="postgres",
    password="admin",
    host="localhost",
    port="5432"
)

# Create cursor and execute query
cursor = conn.cursor()
query = f"""
with base as (
        select gt2.start_timestamp,gt2.tournament_unique_key,gt2.league,gtpp2.tournament_id, case when gtpp2.tournament_id = '7a90ddb8-6dc6-41cc-aa82-e3fd50bbc272' then 'd37feec7-ed2c-4dc5-8ac3-a21a622df1f7' else gtpp2.tournament_id end rewards_tournament_id,gtpp2.player_pic,gtpp2.player_id,gtpp2.player_handle,gtpp2.player_rank,gt2.tournament_name
        ,(gtpp2.db_updated_cst + interval '6 hour')::timestamp as timestamp
    from flatten.get_tournament_past_players gtpp2 
        join flatten.get_tournaments gt2 
            on gtpp2.tournament_id = gt2.tournament_id
   -- where gtpp2.player_handle = '0xthemolt'
       --and gtpp2.tournament_unique_key = 'Main 24'
    order by 1 desc
  )
  ,heroes as (select distinct hero_handle,is_deleted from flatten.GET_HEROS_WITH_STATS_SNAPSHOT where  start_datetime >= '2024-07-01' and hero_handle is not null  and snapshot_rank  = 1)
  ,nbc_wallets as (select distinct player_id from master.nbc_wallets)
  ,historical_rewards as (
  select player_id,tournament_id,tournament_unique_key,league,
	null as decks,/*can't be done with this data*/
	null as itm_decks, /*can't be done with this data*/
	rank as best_rank,
	reward_eth,
	reward_pack,
	reward_fan,
	reward_frag,
	reward_gold,
    is_rewards_final
  from flatten.GET_TOURNAMENT_HISTORIES_BY_PLAYER_ID
  --where player_id = '0x162F95a9364c891028d255467F616902A479681a'
--  and tournament_unique_key = 'Main 25'
)
,historical_rewards_agg as (
select  player_id,tournament_unique_key,
	null as decks,
	COUNT(distinct case when coalesce(reward_pack,0) > 0 then tournament_id end) as itm_decks, /*for each league w/ + 1 card assume at least 1 ITM deck, need this because some rewards history look up are bugged*/
	MIN(case when league = 'Elite' then best_rank  end) as best_elite,
	MIN(case when league = 'Gold' then best_rank  end) as best_gold,
	MIN(case when league = 'Silver' then best_rank  end) as best_silver,
	MIN(case when league = 'Bronze' then best_rank  end) as best_bronze,
	MIN(case when league = 'Reverse' then best_rank  end) as best_reverse,
	MIN(case when league not IN ('Elite','Gold','Silver','Bronze','Reverse') then best_rank  end) as best_other,
	suM(reward_eth) as reward_eth,
	suM(reward_pack) as reward_pack,
	suM(reward_fan) as reward_fan,
	suM(reward_frag) as reward_frag,
	suM(reward_gold) as reward_gold,
    MIN(is_rewards_final) as is_rewards_final
from historical_rewards
group by 1,2
)
,rewards_final as (select tournament_unique_key, MIN(is_rewards_final) as is_rewards_final from historical_rewards_agg group by 1)
,rewards as (
  select gtpp2.tournament_unique_key,
  		gtpp2.player_id,
  		COUNT(*) as decks,
  		SUM(case when (coalesce(reward_pack.reward,0) + (coalesce(reward_frag.reward,0)/100)) >=1 then 1 else 0 END) as itm_decks,
		MIN(case when league = 'Elite' then player_rank  end) as best_elite,
		MIN(case when league = 'Gold' then player_rank  end) as best_gold,
		MIN(case when league = 'Silver' then player_rank  end) as best_silver,
		MIN(case when league = 'Bronze' then player_rank  end) as best_bronze,
		MIN(case when league = 'Reverse' then player_rank  end) as best_reverse,
        sum(coalesce(reward_eth.reward,0)) as reward_eth,
        sum(coalesce(reward_pack.reward,0)) as reward_pack,
        sum(coalesce(reward_fan.reward,0)) as reward_fan,
        sum(coalesce(reward_frag.reward,0)) as reward_frag,
        sum(coalesce(reward_gold.reward,0)) as reward_gold
  from base gtpp2
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_eth
        ON gtpp2.rewards_tournament_id  = reward_eth.tournament_id 
        AND gtpp2.player_rank BETWEEN reward_eth.range_start AND reward_eth.range_end
        AND reward_eth.reward_type = 'ETH'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_pack
        ON gtpp2.rewards_tournament_id = reward_pack.tournament_id 
        AND gtpp2.player_rank BETWEEN reward_pack.range_start AND reward_pack.range_end
        AND reward_pack.reward_type = 'PACK'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_fan
        ON gtpp2.rewards_tournament_id = reward_fan.tournament_id 
        AND gtpp2.player_rank BETWEEN reward_fan.range_start AND reward_fan.range_end
        AND reward_fan.reward_type = 'FAN'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_frag
        ON gtpp2.rewards_tournament_id = reward_frag.tournament_id 
        AND gtpp2.player_rank BETWEEN reward_frag.range_start AND reward_frag.range_end
        AND reward_frag.reward_type = 'FRAGMENT'
        and gtpp2.start_timestamp::date >= '2024-11-09'
  	LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_gold
        ON gtpp2.rewards_tournament_id = reward_gold.tournament_id 
        AND gtpp2.player_rank BETWEEN reward_gold.range_start AND reward_gold.range_end
        AND reward_gold.reward_type = 'GOLD'
   --where gtpp2.tournament_unique_key = 'Main 25'
   group by gtpp2.tournament_unique_key,gtpp2.player_id
 )
,current_main_itm as (
/*only players who meet card criteria*/
select distinct player_id from rewards where tournament_unique_key = 'Main {TOURNAMENT_NUMBER}' group by 1 having sum(coalesce(reward_frag,0)) >= 200 /*current main itm*/
union 
/*add heroes regardless of rewards*/
select distinct player_id from base where tournament_unique_key = 'Main {TOURNAMENT_NUMBER}' and player_handle in (select hero_handle from heroes)
union 
/*add nbc wallets*/
select distinct player_id from nbc_wallets
)
, all_mains as (
select distinct gt.tournament_unique_key,gt.start_timestamp
,case when gt.tournament_status = 'finished' then gt.tournament_unique_key || ' End' else tournament_status end as tournament_status
,gt.tournament_seq_nbr  
,COALESCE(rewards_final.is_rewards_final,0) as is_rewards_final
from flatten.get_tournaments gt
left join rewards_final on 
	gt.tournament_unique_key = rewards_final.tournament_unique_key
where gt.tournament_Status in ('finished','live' )
)
, player_latest as (
	select tournament_unique_key,player_handle,base.player_id,player_pic
	,row_number() over (partition by base.player_id order by start_timestamp desc) as last_pic_seq_nbr  
	,timestamp
	from base join current_main_itm on base.player_id = current_main_itm.player_id 
)
select
	m.tournament_seq_nbr,
    m.tournament_unique_key,
    p.player_pic,
    p.player_handle,
	ARRAY_REMOVE(ARRAY[
	    CASE WHEN h.is_deleted = 1 THEN 0 END,
	    CASE WHEN h.is_deleted = 0 THEN 1 END,
	    CASE WHEN nbc.player_id IS NOT NULL THEN 2 END,
	    CASE WHEN h.is_deleted IS NULL AND nbc.player_id IS NULL THEN 3 END
	], NULL) AS player_types,
    hr.best_elite as elite_rank,
    hr.best_gold as gold_rank,
    hr.best_silver as silver_rank,
    hr.best_bronze as bronze_rank,
    hr.best_reverse as sub_rank,
    hr.best_other as other_rank,
    COALESCE(hr.reward_eth, 0) as reward_eth,
    COALESCE(hr.reward_pack, 0) as reward_pack,
    COALESCE(hr.reward_fan, 0) as reward_fan,
    COALESCE(hr.reward_frag, 0) as reward_frag,
    COALESCE(hr.reward_gold, 0)  as reward_gold,
    COALESCE(r.decks, 0)  as decks, /*still have to use this to get deck itm but it won't be accurate for first few*/
    GREATEST(r.itm_decks,hr.itm_decks) as itm_decks, /*rewards should be more accurate, but in some cases the rewards ranges were overridden or bugged, use the greater of the two*/
    p.timestamp
FROM all_mains m
CROSS join LATERAL (
    SELECT * FROM player_latest
    WHERE last_pic_seq_nbr = 1
) p
left join heroes h
	on p.player_handle = h.hero_handle
left join nbc_wallets nbc
	on p.player_id = nbc.player_id
left join historical_rewards_agg hr
	on p.player_id = hr.player_id
	and m.tournament_unique_key = hr.tournament_unique_key 
left join rewards r
	on p.player_id = r.player_id
	and m.tournament_unique_key = r.tournament_unique_key
where m.tournament_status  <> 'live'
	and m.is_rewards_final = 1
union
select
	m.tournament_seq_nbr,
    m.tournament_unique_key,
    p.player_pic,
    p.player_handle,
	ARRAY_REMOVE(ARRAY[
	    CASE WHEN h.is_deleted = 1 THEN 0 END,
	    CASE WHEN h.is_deleted = 0 THEN 1 END,
	    CASE WHEN nbc.player_id IS NOT NULL THEN 2 END,
	    CASE WHEN h.is_deleted IS NULL AND nbc.player_id IS NULL THEN 3 END
	], NULL) AS player_types,
    r.best_elite as elite_rank,
    r.best_gold as gold_rank,
    r.best_silver as silver_rank,
    r.best_bronze as bronze_rank,
    r.best_reverse as sub_rank,
    null::int as other_rank,
    COALESCE(r.reward_eth, 0) as reward_eth,
    COALESCE(r.reward_pack, 0) as reward_pack,
    COALESCE(r.reward_fan, 0) as reward_fan,
    COALESCE(r.reward_frag, 0) as reward_frag,
    COALESCE(r.reward_gold, 0)  as reward_gold,
    COALESCE(r.decks, 0)  as decks,
    COALESCE(r.itm_decks, 0) as itm_decks,
    p.timestamp
FROM all_mains m
CROSS join LATERAL (
    SELECT * FROM player_latest
    WHERE last_pic_seq_nbr = 1
) p
left join heroes h
	on p.player_handle = h.hero_handle
left join nbc_wallets nbc
	on p.player_id = nbc.player_id
left join rewards r
	on p.player_id = r.player_id
	and m.tournament_unique_key = r.tournament_unique_key
where tournament_status  = 'live' or m.is_rewards_final = 0
and decks <> 0
order by 1
"""
cursor.execute(query)

rows = cursor.fetchall()

# Find the max latest_score_timestamp
max_timestamp = max(row[18] for row in rows if row[18] is not None)

# Convert the results to a list of dictionaries
player_history = []
for row in rows:
    player_handle = row[3]
    player_data = {
        'tournament_seq_nbr': row[0],
        'tournament_unique_key': row[1],
        'player_pic': row[2],
        'player_handle': player_handle,
        'player_type': row[4],
        'elite_rank': row[5],
        'gold_rank': row[6],
        'silver_rank': row[7],
        'bronze_rank': row[8],
        'sub_rank': row[9],
        'other_rank': row[10],
        'reward_eth': float(row[11]) if row[11] else 0.0,
        'reward_pack': int(row[12]) if row[12] else 0,
        'reward_fan': int(row[13]) if row[13] else 0,
        'reward_frag': int(row[14]) if row[14] else 0,
        'reward_gold': int(row[15]) if row[15] else 0,
        'decks': int(row[16]) if row[16] else 0,
        'itm_decks': int(row[17]) if row[17] else 0,
        'timestamp': row[18]
    }
    player_history.append(player_data)

# Create the final JSON structure with metadata
final_data = {
    'metadata': {
        'timestamp': max_timestamp.isoformat() if max_timestamp else None
    },
    'players': player_history
}

# Write the data to JSON
with open('pages/player_tournament_history.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=2, default=str)

print("Player tournament history has been successfully written to JSON.")
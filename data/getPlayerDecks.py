import psycopg2
import json
import os
from datetime import datetime

# Load configuration from config.json
with open('C:/fantasy_top_analysis/pages/config.json', 'r') as config_file:
    config = json.load(config_file)

TOURNAMENT_NUMBER = config['tournament_number']
LEAGUE_IMAGES = config['league_images']
LEAGUE_COLORS = config['league_colors']
REWARD_IMAGES = config['reward_images']

def get_db_connection():
    return psycopg2.connect(
        dbname="0xthemolt",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

#get the tournament status
conn = get_db_connection()
cursor = conn.cursor()
query = f"""select max(tournament_status) as tournament_status from flatten.get_tournaments where  tournament_unique_key  = 'Main {TOURNAMENT_NUMBER}'"""
cursor.execute(query)
rows = cursor.fetchall()
tournament_status = rows[0][0] if rows else None
cursor.close()

# Create cursor and execute query
cursor = conn.cursor()
query = f"""
WITH ordered_records AS (
SELECT fantasy_score as score,tournament_rank as rank, ROW_NUMBER() OVER (ORDER BY base.fantasy_Score DESC) AS row_num,hero_handle
FROM flatten.GET_HEROS_WITH_STATS_TOURNAMENT base 
join flatten.get_tournaments gt 
	on base.tournament_id = gt.tournament_id 
where gt.tournament_league_unique_key = 'Elite Main {TOURNAMENT_NUMBER}'
)
,hero_count as (select COUNT(*) as hero_count from ordered_records)
,new_hero_stars as (
select hero_handle,
        score,rank,
        CASE             
            WHEN row_num <= (hc.hero_count * .07) THEN 8
            WHEN row_num <= (hc.hero_count * .18) THEN 7
            WHEN row_num <= (hc.hero_count * .32) THEN 6
            WHEN row_num <= (hc.hero_count * .50) THEN 5
            WHEN row_num <= (hc.hero_count * .68) THEN 4
            WHEN row_num <= (hc.hero_count * .82) THEN 3
            WHEN row_num <= (hc.hero_count * .93) THEN 2
            ELSE 1
        end new_hero_stars
    FROM ordered_records 
    CROSS JOIN hero_count hc
)
,trade_history_base as (
select buyer_id,card_id,timestamp,price,hero_rarity_id,hero_id,rarity,hero_handle,row_number() over (partition by buyer_id,card_id order by timestamp desc) buyer_last_buy_card_id
from flatten.get_hero_last_trades ghlt 
where buyer_id  not in ('0x000000000000000000000000000000000000000A','0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841') --frag buy
)
,trade_history_prior_to_tournament as (
select buyer_id,hero_rarity_id,hero_id,price,rarity,hero_handle
,ROW_NUMBER() over (partition by hero_rarity_id order by timestamp desc) hero_rarity_trade_history_rank
,timestamp
from trade_history_base
where 1=1  
and timestamp >= NOW() at time zone 'UTC' - interval '21 days'  --for performance
 and timestamp < (select start_timestamp from  flatten.get_tournaments where tournament_league_unique_key  = 'Elite Main {TOURNAMENT_NUMBER}') --pre main start
-- and hero_handle = 'blockgraze' and rarity = 'rare'
)
,trade_l5_txn_median as (
select hero_id,hero_rarity_id,rarity,PERCENTILE_CONT(0.5) within group(	order by price) as median_price	
from trade_history_prior_to_tournament
where hero_rarity_trade_history_rank <= 5
group by 1,2,3
)
    select gt.tournament_name as league_name,gtpp.tournament_league_unique_key,gt.tournament_duration_hours::integer as tournament_duration_hours,
        case when gt.tournament_status  = 'live'   
            then ROUND(EXTRACT(EPOCH FROM (NOW() at time zone 'UTC' - gt.start_timestamp)) / 3600)::integer
        else ROUND(gt.tournament_duration_hours)::integer
        end        AS tournament_progress_hours,
        player_handle,player_pic,player_score,player_rank,  
           card1_hero_handle,card1_picture_url,ROUND(card1_fantasy_score,0) card1_score,card1_hero_stars,card1_new_hero_stars.new_hero_stars,buyer_cost_card1.price as card1_actual_cost,market_l5_cost_card1.median_price as card1_market_cost
           		,case when card1_hero_rarity = 'rare' then (common_market_l5_cost_card1.median_price * .85) * 5 when card1_hero_rarity = 'epic' then  (common_market_l5_cost_card1.median_price * .80) * 25  when card1_hero_rarity = 'legendary' then (common_market_l5_cost_card1.median_price * .75) * 125  else common_market_l5_cost_card1.median_price end as card1_est_cost,
           card2_hero_handle,card2_picture_url,ROUND(card2_fantasy_score,0) card2_score,card2_hero_stars,card2_new_hero_stars.new_hero_stars,buyer_cost_card2.price as card2_actual_cost,market_l5_cost_card2.median_price as card2_market_cost
           		,case when card2_hero_rarity = 'rare' then (common_market_l5_cost_card2.median_price * .85) * 5 when card2_hero_rarity = 'epic' then  (common_market_l5_cost_card2.median_price * .80) * 25  when card2_hero_rarity = 'legendary' then (common_market_l5_cost_card2.median_price * .75) * 125  else common_market_l5_cost_card2.median_price end as card2_est_cost,
           card3_hero_handle,card3_picture_url,ROUND(card3_fantasy_score,0) card3_score,card3_hero_stars,card3_new_hero_stars.new_hero_stars,buyer_cost_card3.price as card3_actual__cost,market_l5_cost_card3.median_price as card3_market_cost
           		,case when card3_hero_rarity = 'rare' then (common_market_l5_cost_card3.median_price * .85) * 5 when card3_hero_rarity = 'epic' then  (common_market_l5_cost_card3.median_price * .80) * 25  when card3_hero_rarity = 'legendary' then (common_market_l5_cost_card3.median_price * .75) * 125  else common_market_l5_cost_card3.median_price end as card3_est_cost,
           card4_hero_handle,card4_picture_url,ROUND(card4_fantasy_score,0) card4_score,card4_hero_stars,card4_new_hero_stars.new_hero_stars,buyer_cost_card4.price as card4_actual_cost,market_l5_cost_card4.median_price as card4_market_cost
           		,case when card4_hero_rarity = 'rare' then (common_market_l5_cost_card4.median_price * .85) * 5 when card4_hero_rarity = 'epic' then  (common_market_l5_cost_card4.median_price * .80) * 25  when card4_hero_rarity = 'legendary' then (common_market_l5_cost_card4.median_price * .75) * 125  else common_market_l5_cost_card4.median_price end as card4_est_cost,
           card5_hero_handle,card5_picture_url,ROUND(card5_fantasy_score,0) card5_score,card5_hero_stars,card5_new_hero_stars.new_hero_stars,buyer_cost_card5.price as card5_actual_cost,market_l5_cost_card5.median_price as card5_market_cost
           		,case when card5_hero_rarity = 'rare' then (common_market_l5_cost_card5.median_price * .85) * 5 when card5_hero_rarity = 'epic' then  (common_market_l5_cost_card5.median_price * .80) * 25  when card5_hero_rarity = 'legendary' then (common_market_l5_cost_card5.median_price * .75) * 125  else common_market_l5_cost_card5.median_price end as card5_est_cost,
           tournament_player_deck_id,
           reward_fan.reward as fan,
			reward_gold.reward AS gold,
			reward_eth.reward AS eth,
			reward_pack.reward AS packs,
            reward_frag.reward AS frag,
            gtpp.db_updated_cst::timestamp + interval '6 hour' as  timestamp
    from flatten.get_tournament_past_players gtpp
    join flatten.get_tournaments gt
        on gtpp.tournament_id = gt.tournament_id
    left join flatten.GET_TOURNAMENT_BY_ID reward_gold
       ON gtpp.tournament_id = reward_gold.tournament_id
        AND gtpp.unique_player_rank between reward_gold.range_start and reward_gold.range_end
        AND reward_gold.reward_type = 'GOLD'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_eth
       ON gtpp.tournament_id = reward_eth.tournament_id
        AND gtpp.unique_player_rank between reward_eth.range_start and reward_eth.range_end
        AND reward_eth.reward_type = 'ETH'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_pack
       ON gtpp.tournament_id = reward_pack.tournament_id
        AND gtpp.unique_player_rank between reward_pack.range_start and reward_pack.range_end
        AND reward_pack.reward_type = 'PACK'
   LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_fan
       ON gtpp.tournament_id = reward_fan.tournament_id
        AND gtpp.unique_player_rank between reward_fan.range_start and reward_fan.range_end
        AND reward_fan.reward_type = 'FAN'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_frag
        ON gtpp.tournament_id = reward_frag.tournament_id
        AND gtpp.unique_player_rank between reward_frag.range_start and reward_frag.range_end
        AND reward_frag.reward_type = 'FRAGMENT'
    LEFT JOIN new_hero_stars card1_new_hero_stars
        on gtpp.card1_hero_handle = card1_new_hero_stars.hero_handle
    LEFT JOIN new_hero_stars card2_new_hero_stars
        on gtpp.card2_hero_handle = card2_new_hero_stars.hero_handle
    LEFT JOIN new_hero_stars card3_new_hero_stars
        on gtpp.card3_hero_handle = card3_new_hero_stars.hero_handle
    LEFT JOIN new_hero_stars card4_new_hero_stars
        on gtpp.card4_hero_handle = card4_new_hero_stars.hero_handle
    LEFT JOIN new_hero_stars card5_new_hero_stars
        on gtpp.card5_hero_handle = card5_new_hero_stars.hero_handle
    left join trade_history_base  buyer_cost_card1
    	on gtpp.card1_id = buyer_cost_card1.card_id
    	and gtpp.player_id = buyer_cost_card1.buyer_id
		and buyer_cost_card1.buyer_last_buy_card_id = 1
    left join trade_history_base  buyer_cost_card2
    	on gtpp.card2_id = buyer_cost_card2.card_id
    	and gtpp.player_id = buyer_cost_card2.buyer_id
		and buyer_cost_card2.buyer_last_buy_card_id = 1
    left join trade_history_base  buyer_cost_card3
    	on gtpp.card3_id = buyer_cost_card3.card_id
    	and gtpp.player_id = buyer_cost_card3.buyer_id
		and buyer_cost_card3.buyer_last_buy_card_id = 1
    left join trade_history_base  buyer_cost_card4
    	on gtpp.card4_id = buyer_cost_card4.card_id
    	and gtpp.player_id = buyer_cost_card4.buyer_id
		and buyer_cost_card4.buyer_last_buy_card_id = 1
    left join trade_history_base  buyer_cost_card5
    	on gtpp.card5_id = buyer_cost_card5.card_id
    	and gtpp.player_id = buyer_cost_card5.buyer_id
		and buyer_cost_card5.buyer_last_buy_card_id = 1
	left join trade_l5_txn_median market_l5_cost_card1
		on gtpp.card1_hero_rarity_index = market_l5_cost_card1.hero_rarity_id
	left join trade_l5_txn_median market_l5_cost_card2
		on gtpp.card2_hero_rarity_index = market_l5_cost_card2.hero_rarity_id
	left join trade_l5_txn_median market_l5_cost_card3
		on gtpp.card3_hero_rarity_index = market_l5_cost_card3.hero_rarity_id
	left join trade_l5_txn_median market_l5_cost_card4
		on gtpp.card4_hero_rarity_index = market_l5_cost_card4.hero_rarity_id
	left join trade_l5_txn_median market_l5_cost_card5
		on gtpp.card5_hero_rarity_index = market_l5_cost_card5.hero_rarity_id
	left join trade_l5_txn_median common_market_l5_cost_card1
		on gtpp.card1_hero_id = common_market_l5_cost_card1.hero_id
		and common_market_l5_cost_card1.rarity = 'common'
	left join trade_l5_txn_median common_market_l5_cost_card2
		on gtpp.card2_hero_id = common_market_l5_cost_card2.hero_id
		and common_market_l5_cost_card2.rarity = 'common'
	left join trade_l5_txn_median common_market_l5_cost_card3
		on gtpp.card3_hero_id = common_market_l5_cost_card3.hero_id
		and common_market_l5_cost_card3.rarity = 'common'
	left join trade_l5_txn_median common_market_l5_cost_card4
		on gtpp.card4_hero_id = common_market_l5_cost_card4.hero_id
		and common_market_l5_cost_card4.rarity = 'common'
	left join trade_l5_txn_median common_market_l5_cost_card5
		on gtpp.card5_hero_id = common_market_l5_cost_card5.hero_id
		and common_market_l5_cost_card5.rarity = 'common'
    where gtpp.tournament_unique_key = 'Main {TOURNAMENT_NUMBER}'
    order by player_score desc
"""
cursor.execute(query)

rows = cursor.fetchall()

optimal_decks_query = f"""
with current_mains as (
    select tournament_id,tournament_league_unique_key,tournament_name,star_cap,legendary_cap,epic_cap,rare_cap,common_cap,
       CASE 
        WHEN tournament_status = 'finished' THEN 100
        ELSE LEAST(ROUND(
                EXTRACT(EPOCH FROM (NOW() AT TIME ZONE 'UTC' - start_timestamp::timestamp)) / 
                (tournament_duration_hours * 3600) * 100
            ),100)
   	END as tournament_pct_complete
    from flatten.get_tournaments gt
    where tournament_unique_key = 'Main {TOURNAMENT_NUMBER}'
    )
   	,base as (
    select gt.tournament_name as league_name,gtpp.tournament_league_unique_key,player_handle,player_id
    	--,player_pic
    		,player_score,player_rank,
          -- card1_picture_url,
           ROUND(card1_fantasy_score,0) card1_score,
           --card2_picture_url,
           ROUND(card2_fantasy_score,0) card2_score,
           --card3_picture_url,
           ROUND(card3_fantasy_score,0) card3_score,
           --card4_picture_url,
           ROUND(card4_fantasy_score,0) card4_score,
           --card5_picture_url,
           ROUND(card5_fantasy_score,0) card5_score,
           case when card1_hero_rarity = 'rare' then 1 else 0 end +
           case when card2_hero_rarity = 'rare' then 1 else 0 end +
           case when card3_hero_rarity = 'rare' then 1 else 0 end +
           case when card4_hero_rarity = 'rare' then 1 else 0 end +
           case when card5_hero_rarity = 'rare' then 1 else 0 end
           as rare_cards,
           case when card1_hero_rarity = 'epic' then 1 else 0 end +
           case when card2_hero_rarity = 'epic' then 1 else 0 end +
           case when card3_hero_rarity = 'epic' then 1 else 0 end +
           case when card4_hero_rarity = 'epic' then 1 else 0 end +
           case when card5_hero_rarity = 'epic' then 1 else 0 end
           as epic_cards,
            case when card1_hero_rarity = 'legendary' then 1 else 0 end +
           case when card2_hero_rarity = 'legendary' then 1 else 0 end +
           case when card3_hero_rarity = 'legendary' then 1 else 0 end +
           case when card4_hero_rarity = 'legendary' then 1 else 0 end +
           case when card5_hero_rarity = 'legendary' then 1 else 0 end
           as legendary_cards,
           card1_hero_stars + card2_hero_stars + card3_hero_stars + card4_hero_stars + card5_hero_stars  as deck_stars,
           tournament_player_deck_id,
           reward_fan.reward as fan,
			reward_gold.reward AS gold,
			reward_eth.reward AS eth,
			reward_pack.reward AS packs
    from flatten.get_tournament_past_players gtpp
    join flatten.get_tournaments gt
        on gtpp.tournament_id = gt.tournament_id
    left join flatten.GET_TOURNAMENT_BY_ID reward_gold
       ON gtpp.tournament_id = reward_gold.tournament_id
        AND gtpp.unique_player_rank between reward_gold.range_start and reward_gold.range_end
        AND reward_gold.reward_type = 'GOLD'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_eth
       ON gtpp.tournament_id = reward_eth.tournament_id
        AND gtpp.unique_player_rank between reward_eth.range_start and reward_eth.range_end
        AND reward_eth.reward_type = 'ETH'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_pack
       ON gtpp.tournament_id = reward_pack.tournament_id
        AND gtpp.unique_player_rank between reward_pack.range_start and reward_pack.range_end
        AND reward_pack.reward_type = 'PACK'
   LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_fan
       ON gtpp.tournament_id = reward_fan.tournament_id
        AND gtpp.unique_player_rank between reward_fan.range_start and reward_fan.range_end
        AND reward_fan.reward_type = 'FAN'
    where gtpp.tournament_unique_key = 'Main {TOURNAMENT_NUMBER}'
    --and gtpp.player_handle = '0xTactic'
    and CASE 
        WHEN gt.tournament_status = 'finished' THEN 100
        ELSE LEAST(ROUND(
                EXTRACT(EPOCH FROM (NOW() AT TIME ZONE 'UTC' - gt.start_timestamp::timestamp)) / 
                (gt.tournament_duration_hours * 3600) * 100
            ),100)
   	END >= 50 -- tournament_pct_complete
    )
    --select * from base;
 ,league_finder as (
    select b.player_id,
    	b.tournament_league_unique_key,tournament_player_deck_id,player_rank,player_score,eth,packs
    	,deck_stars,rare_cards,epic_cards,legendary_cards
    	,reverse.tournament_id as is_valid_reverse_id
    	,bronze.tournament_id as is_valid_bronze_id
    	,silver.tournament_id as is_valid_silver_id
    	,gold.tournament_id as is_valid_gold_id
    	,elite.tournament_id as is_valid_elite_id
    from base b
   left join current_mains as reverse 
    	on b.deck_stars >= reverse.star_cap /*has to be above cap*/
    	and b.rare_cards = 0  /*no rares*/
    	and b.epic_cards = 0  /*no epics*/
    	and b.legendary_cards = 0 /*no legendary*/
    	and b.league_name <> 'Reverse Score'
    	and reverse.tournament_name = 'Reverse Score'
    left join current_mains as bronze 
    	on b.deck_stars <= bronze.star_cap
    	and b.rare_cards = 0  /*no rares*/
    	and b.epic_cards = 0  /*no epics*/
        and b.legendary_cards = 0 /*no legendary*/
    	and b.league_name <> 'Bronze'
    	and bronze.tournament_name = 'Bronze'
    left join current_mains as silver 
    	on b.deck_stars <= silver.star_cap
    	and b.rare_cards <= silver.rare_cap
    	and b.epic_cards <=  0  /*no epics*/
        and b.legendary_cards = 0 /*no legendary*/
    	and b.league_name <> 'Silver'
    	and silver.tournament_name = 'Silver'
    left join current_mains as gold 
    	on b.deck_stars <= gold.star_cap
    	and b.rare_cards <= gold.rare_cap
    	and b.epic_cards <= gold.epic_cap
        and b.legendary_cards = 0 /*no legendary*/
    	and b.league_name <> 'Gold'
    	and gold.tournament_name = 'Gold'
    left join current_mains as elite 
    	ON b.league_name <> 'Elite'
    	and elite.tournament_name = 'Elite'
   -- where player_handle = '0xthemolt'
    --and tournament_player_deck_id = 'Silver Main 24 | 0x162F95a9364c891028d255467F616902A479681a | 246'
    )
  ,rank_new_bronze as (
  select *,row_number() over (order by player_score desc) as new_player_rank
  from (
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,null as player_rank,deck_stars,rare_cards,epic_cards,legendary_cards,is_valid_bronze_id as tournament_id
	  from league_finder
	  where is_valid_bronze_id is not null /*valid decks that could be in silver but aren't*/
	  union all
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,player_rank,null as deck_stars,null as rare_cards,null as epic_cards,null as legendary_cards,tournament_id
	  from flatten.get_tournament_past_players 
	  where tournament_league_unique_key  = 'Bronze Main {TOURNAMENT_NUMBER}' 
  ) 
  )
  ,rank_new_silver as (
  select *,row_number() over (order by player_score desc) as new_player_rank
  from (
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,null as player_rank,deck_stars,rare_cards,epic_cards,legendary_cards,is_valid_silver_id as tournament_id
	  from league_finder
	  where is_valid_silver_id is not null /*valid decks that could be in silver but aren't*/
	  union all
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,player_rank,null as deck_stars,null as rare_cards,null as epic_cards,null as legendary_cards,tournament_id
	  from flatten.get_tournament_past_players 
	  where tournament_league_unique_key  = 'Silver Main {TOURNAMENT_NUMBER}' 
  ) 
  )
  ,rank_new_gold as (
  select *,row_number() over (order by player_score desc) as new_player_rank
  from (
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,null as player_rank,deck_stars,rare_cards,epic_cards,legendary_cards,is_valid_gold_id as tournament_id
	  from league_finder
	  where is_valid_gold_id is not null /*valid decks that could be in gold but aren't*/
	  union all
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,player_rank,null as deck_stars,null as rare_cards,null as epic_cards,null as legendary_cards,tournament_id
	  from flatten.get_tournament_past_players 
	  where tournament_league_unique_key  = 'Gold Main {TOURNAMENT_NUMBER}'
  )
 )
   ,rank_new_elite as (
  select *,row_number() over (order by player_score desc) as new_player_rank
  from (
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,null as player_rank,deck_stars,rare_cards,epic_cards,legendary_cards,is_valid_elite_id as tournament_id
	  from league_finder
	  where is_valid_elite_id is not null /*valid decks that could be in elite but aren't*/
	  union all
	  select player_id,tournament_league_unique_key,tournament_player_deck_id,player_score,player_rank,null as deck_stars,null as rare_cards,null as epic_cards,null as legendary_cards,tournament_id
	  from flatten.get_tournament_past_players 
	  where tournament_league_unique_key  = 'Elite Main {TOURNAMENT_NUMBER}'
  )
  )
  , union_all as (
   select * from rank_new_bronze where  player_rank is null  /*deck from other league*/
   union
  select * from rank_new_silver where  player_rank is null /*deck from other league*/
  union all
  select * from rank_new_gold where  player_rank is null  /*deck from other league*/
  union all
   select * from rank_new_elite where  player_rank is null /*deck from other league*/
  )
  ,final as (
 select b.player_id,b.tournament_league_unique_key,b.tournament_player_deck_id,b.player_rank,b.player_score,b.eth,b.packs
    	,b.deck_stars
 ,new_gt.tournament_league_unique_key as newtournament_league_unique_key,union_all.new_player_rank,reward_eth.reward AS new_eth,reward_pack.reward AS new_packs
 ,case when coalesce(reward_eth.reward,0) > b.eth then 1 else 0 end as is_new_eth_higher
  ,case when coalesce(reward_pack.reward,0) > b.packs then 1 else 0 end as is_new_packs_higher
  ,case when coalesce(reward_eth.reward,0) > b.eth then 1 /*eth higher*/
  	when coalesce(b.eth,0) = 0 and coalesce(reward_pack.reward,0) > b.packs then 1 /*didn't with eth and packs higher*/
  	else 0 end is_new_better
 from league_finder b
 left join union_all
 	on b.tournament_player_deck_id = union_all.tournament_player_deck_id
 left join flatten.get_tournaments new_gt
 	on union_all.tournament_id = new_gt.tournament_id
 LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_eth
   ON union_all.tournament_id = reward_eth.tournament_id
    AND union_all.new_player_rank between reward_eth.range_start and reward_eth.range_end
    AND reward_eth.reward_type = 'ETH'
    and union_all.player_rank is null /*real deck don't use*/
LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_pack
   ON union_all.tournament_id = reward_pack.tournament_id
    AND union_all.new_player_rank between reward_pack.range_start and reward_pack.range_end
    AND reward_pack.reward_type = 'PACK'
     and union_all.player_rank is null /*real deck don't use*/
     )
     select tournament_player_deck_id
     ,newtournament_league_unique_key as optimal_league
     ,new_player_rank as optimal_rank
     ,new_eth
     ,new_packs
     from final
     where is_new_better = 1
 order by player_score desc
"""
cursor.execute(optimal_decks_query)
rows_optimal = cursor.fetchall()

# Create a dictionary of optimal deck data for faster lookup
optimal_decks_dict = {
    row[0]: {
        'optimal_league': row[1],
        'optimal_rank': row[2],
        'new_eth': float(row[3]) if row[3] else 0.0,
        'new_packs': int(row[4]) if row[4] else 0
    } for row in rows_optimal
}

# Debug: Print first 5 entries from optimal_decks_dict
print("\nFirst 5 entries in optimal_decks_dict:")
for i, (deck_id, data) in enumerate(list(optimal_decks_dict.items())[:5]):
    print(f"{i+1}. Deck ID: {deck_id}")
    print(f"   Optimal League: {data['optimal_league']}")
    print(f"   Optimal Rank: {data['optimal_rank']}")
    print(f"   New ETH: {data['new_eth']}")
    print(f"   New Packs: {data['new_packs']}")
    print("---")

# Debug: Print first 5 matches where optimal_league exists
print("\nFirst 5 matches with optimal league:")
match_count = 0
for row in rows:
    tournament_player_deck_id = row[33]
    optimal_data = optimal_decks_dict.get(tournament_player_deck_id, {})
    
    if optimal_data.get('optimal_league') is not None:
        match_count += 1
        print(f"\nMatch {match_count}:")
        print(f"Player: {row[4]}")  # player_handle is at index 4
        print(f"Deck ID: {tournament_player_deck_id}")
        print(f"Current League: {row[1]}")  # tournament_league_unique_key is at index 1
        print(f"Optimal League: {optimal_data['optimal_league']}")
        print(f"Current Rank: {row[7]}")  # player_rank is at index 7
        print(f"Optimal Rank: {optimal_data['optimal_rank']}")
        
        if match_count >= 5:
            break

print(f"\nTotal matches found: {match_count}")

def calculate_rarity_score(picture_url, fantasy_score):
    if not fantasy_score:
        return None
    if 'legendary' in picture_url.lower():
        return fantasy_score * 2.5
    elif 'epic' in picture_url.lower():
        return fantasy_score * 2.0
    elif 'rare' in picture_url.lower():
        return fantasy_score * 1.5
    return fantasy_score

# Create metadata from first row
metadata = {
    'tournament_duration_hours': float(rows[0][2]) if rows[0][2] else None,
    'tournament_progress_hours': rows[0][3],
    'timestamp': rows[0][54]
}

# Convert the results to a list of dictionaries with merged optimal data
player_decks = []
for row in rows:
    tournament_player_deck_id = row[33]
    optimal_data = optimal_decks_dict.get(tournament_player_deck_id, {})
    
    player_deck = {
        'league_name': row[0],
        'tournament_league_unique_key': row[1],
        'player_handle': row[4],
        'player_pic': row[5],
        'player_score': float(row[6]) if row[6] else None,
        'player_rank': row[7],
        'cards': [
            {
                'hero_handle': row[8],
                'picture_url': row[9], 
                'fantasy_score': float(row[10]) if row[10] else None,
                'rarity_score': calculate_rarity_score(row[9], float(row[10]) if row[10] else None),
                'hero_stars': int(row[11]) if row[11] else 0,
                'new_hero_stars': int(row[12]) if row[12] else 0,
                'actual_card_cost': float(row[13]) if row[13] else None,
                'market_card_cost': float(row[14]) if row[14] else None,
                'est_card_cost': float(row[15]) if row[15] else None
            },
            {
                'hero_handle': row[16],
                'picture_url': row[17], 
                'fantasy_score': float(row[18]) if row[18] else None,
                'rarity_score': calculate_rarity_score(row[17], float(row[18]) if row[18] else None),
                'hero_stars': int(row[19]) if row[19] else 0,
                'new_hero_stars': int(row[20]) if row[20] else 0,
                'actual_card_cost': float(row[21]) if row[21] else None,
                'market_card_cost': float(row[22]) if row[22] else None,
                'est_card_cost': float(row[23]) if row[23] else None
            },
            {
                'hero_handle': row[24],
                'picture_url': row[25], 
                'fantasy_score': float(row[26]) if row[26] else None,
                'rarity_score': calculate_rarity_score(row[25], float(row[26]) if row[26] else None),
                'hero_stars': int(row[27]) if row[27] else 0,
                'new_hero_stars': int(row[28]) if row[28] else 0,
                'actual_card_cost': float(row[29]) if row[29] else None,
                'market_card_cost': float(row[30]) if row[30] else None,
                'est_card_cost': float(row[31]) if row[31] else None
            },
            {
                'hero_handle': row[32],
                'picture_url': row[33], 
                'fantasy_score': float(row[34]) if row[34] else None,
                'rarity_score': calculate_rarity_score(row[33], float(row[34]) if row[34] else None),
                'hero_stars': int(row[35]) if row[35] else 0,
                'new_hero_stars': int(row[36]) if row[36] else 0,
                'actual_card_cost': float(row[37]) if row[37] else None,
                'market_card_cost': float(row[38]) if row[38] else None,
                'est_card_cost': float(row[39]) if row[39] else None
            },
            {
                'hero_handle': row[40],
                'picture_url': row[41], 
                'fantasy_score': float(row[42]) if row[42] else None,
                'rarity_score': calculate_rarity_score(row[41], float(row[42]) if row[42] else None),
                'hero_stars': int(row[43]) if row[43] else 0,
                'new_hero_stars': int(row[44]) if row[44] else 0,
                'actual_card_cost': float(row[45]) if row[45] else None,
                'market_card_cost': float(row[46]) if row[46] else None,
                'est_card_cost': float(row[47]) if row[47] else None
            },
        ],
        'tournament_player_deck_id': row[48],
        'fan': int(row[49]) if row[49] else 0,
        'gold': int(row[50]) if row[50] else 0,
        'eth': float(row[51]) if row[51] else 0.0,
        'packs': int(row[52]) if row[52] else 0,
        'frag': int(row[53]) if row[53] else 0,
        'timestamp': row[54].isoformat() if row[54] else None
    }
    player_decks.append(player_deck)

# Sort player_decks by player_handle and then player_rank before creating the final structure
player_decks.sort(key=lambda x: (x['player_handle'], x['player_rank']))


metadata = {
    'tournament_duration_hours': float(rows[0][2]) if rows[0][2] else None,
    'tournament_progress_hours': rows[0][3],
    'timestamp': rows[0][54].isoformat() if rows[0][54] else None  # Convert datetime to ISO format string
}

# Create the final structure
output_data = {
    'metadata': metadata,
    'league_results': player_decks
}

try:
    # Get the absolute path for the output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'tournaments')

    # Ensure the tournaments directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Write to JSON file using absolute path
    output_file = os.path.join(output_dir, 'player_decks.json')
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)

    print(f"Successfully wrote data to: {output_file}")

except Exception as e:
    print(f"Error writing data to file: {str(e)}")
finally:
    # Close the final connection
    conn.close()

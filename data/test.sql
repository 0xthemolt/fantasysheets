-- Active: 1736043764037@@localhost@5432@0xthemolt
with tournaments as (
select  player_id
,count(distinct tournament_unique_key) mains_played
,couNT(*) as deck_count
--,sum(case when player_rank <= 10 then 1 else 0 end) as top_ten_finish_count
from flatten.get_tournament_past_players gtpp 
--where player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and tournament_unique_key = 'Main 32'
group by 1
)
,eth_frags_won as (
select player_id
--,tournament_unique_key
,suM(reward_eth) reward_eth
,sum(reward_frag) + sum(reward_pack * 100) reward_frag 
from flatten.get_tournament_histories_by_player_id 
where player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and tournament_unique_key = 'Main 31'
group by 1--,2
--having suM(reward_eth) <> 0
)
,touranment_rankings as (
select t.tournament_unique_key ,t.league ,t.registered_decks,t.start_timestamp
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
where 1=1
--and tplayers.player_id = '0x162F95a9364c891028d255467F616902A479681a'
--and t.tournament_unique_key  = 'Main 31'
and t.start_timestamp >= '2024-07-01'
)
,league_ranking as (
select league,player_id
,avg(normalized_rank) as avg_best_deck_norm_rank
from touranment_rankings
where best_deck_rank = 1
group by 1,2
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
    where buyer <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
    GROUP BY 1, 2
    
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
    where buyer <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
    GROUP BY 1, 2
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
,suM(eth_won.reward_eth)reward_eth
,suM(coalesce(players.portfolio_value,0)) as portfolio
,sum(players.fan_pts + referral_pts) fan_pts
,sum(players.gold) gold
,suM(players.stars) stars
,sum(tournaments.deck_count) as decks
,suM(players.number_of_cards) as cards
,max(touranment_rankings_elite.avg_best_deck_norm_rank) as elite_norm_rank
,max(touranment_rankings_gold.avg_best_deck_norm_rank) as gold_norm_rank
,max(touranment_rankings_silver.avg_best_deck_norm_rank) as silver_norm_rank
,max(touranment_rankings_bronze.avg_best_deck_norm_rank) as bronze_norm_rank
,max(touranment_rankings_reverse.avg_best_deck_norm_rank) as reverse_norm_rank
,max(coalesce(tvbp.buy_volume,0)) as buy_vol
,max(coalesce(tvbp.sell_volume,0)) as sell_vol
,max(coalesce(tvbp.trade_count,0)) as trade_count
,max(coalesce(tvbp.max_buy,0)) as max_buy
,max(coalesce(tvbp.max_sell,0)) as max_sell
,max(coalesce(tvbp.longest_trading_streak,0)) as longest_trade_streak
,max(updated) freshness_timestamp
from flatten.get_player_basic_data players
join eth_won
	on players.player_id = eth_won.player_id
join tournaments 
	on players.player_id  = tournaments.player_id
left join trade_volume_by_player tvbp
	on players.player_id = tvbp.player_id
left join league_ranking touranment_rankings_diamond
    on players.player_id = touranment_rankings_diamond.player_id
    and touranment_rankings_diamond.league = 'Diamond'
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
where players.player_id = '0x162F95a9364c891028d255467F616902A479681a'
--	and t_hist.tournament_unique_key  = 'Main 32'
group by 1,2,3,4
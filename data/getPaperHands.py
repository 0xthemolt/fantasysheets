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

query = """WITH active_buyers AS (
    SELECT buyer_id,COUNT(*)
    FROM flatten.get_hero_last_trades
    WHERE timestamp >= NOW() - interval '5 weeks'
    GROUP BY buyer_id
    HAVING COUNT(*) >= 8
)
--select count(*) from active_buyers;
,player_sales AS (
    SELECT 
        sell.seller,
        sell.card_id,
        sell.hero_rarity_id,
        sell.hero_handle,
        sell.card_picture,
        sell.seller_id,
        sell.price AS sell_price,
        sell.timestamp::date AS sell_timestamp,
        sell.tx_hash as sell_tx_hash,
        FIRST_VALUE(buy.tx_hash) OVER (
		      PARTITION BY sell.tx_hash 
		      ORDER BY buy.timestamp DESC
		    ) as buy_tx_hash,
	    FIRST_VALUE(buy.timestamp) OVER (
		      PARTITION BY sell.tx_hash 
		      ORDER BY buy.timestamp DESC
		    ) as buy_timestamp,
	    FIRST_VALUE(buy.price) OVER (
		      PARTITION BY sell.tx_hash 
		      ORDER BY buy.price DESC
		    ) as buy_price
    FROM flatten.get_hero_last_trades sell
    left join flatten.get_hero_last_trades buy
    	on sell.seller_id  = buy.buyer_id
    	and sell.card_id = buy.card_id
    	and buy.timestamp < sell.timestamp
    WHERE 1=1
    --and sell.seller in ('0xTactic', '0xthemolt','Khallid4397')
    and sell.buyer_id <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841' /*exclude burn buyer*/
    --and sell.hero_handle  ilike '%orangie%'
    AND sell.seller_id IN (SELECT buyer_id FROM active_buyers)
),
--SELECT * from player_sales;
latest_prices AS (
    SELECT 
        buyer,
        hero_rarity_id,
        price AS last_sold_price,
        timestamp AS last_sold_timestamp,
        tx_hash last_sold_tx_hash
    FROM flatten.get_hero_last_trades
    WHERE hero_rarity_trade_history_rank = 1
),
paperhands AS (
    SELECT 
        bs.seller as player,
        REPLACE(pd.profile_picture, 'https://pbs.twimg.com/profile_images/', '') as player_pfp,
        bs.hero_handle as hero,
        SUBSTRING(bs.card_picture FROM '/v[12]/(.*)') as hero_card,
        bs.buy_tx_hash,
        bs.buy_timestamp,
        bs.buy_price,
        bs.sell_tx_hash,
        bs.sell_price,
        bs.sell_timestamp,
        case when bs.buy_price is not null then bs.sell_price - bs.buy_price else null end as trade_pnl,
        case when lp.last_sold_price > bs.sell_price and lp.last_sold_timestamp > bs.sell_timestamp then lp.last_sold_price else null end as last_sold_price,
        case when lp.last_sold_price > bs.sell_price and lp.last_sold_timestamp > bs.sell_timestamp then lp.last_sold_timestamp else null end as    last_sold_timestamp,
        case when lp.last_sold_price > bs.sell_price and lp.last_sold_timestamp > bs.sell_timestamp then lp.last_sold_tx_hash   else null end as last_sold_tx_hash,
        case when lp.last_sold_price > bs.sell_price and lp.last_sold_timestamp > bs.sell_timestamp then lp.last_sold_price - bs.sell_price else 0 end as paperhanded
    FROM player_sales bs
    JOIN latest_prices lp ON bs.hero_rarity_id = lp.hero_rarity_id
    left join flatten.get_player_basic_data pd
    	on bs.seller_id = pd.player_id
--    WHERE lp.last_sold_price > bs.sell_price
--    AND lp.last_sold_timestamp > bs.sell_timestamp
    ORDER BY sell_timestamp desc
)
SELECT 
    *,
    -- All-time rankings (partitioned by player)
    CASE WHEN trade_pnl IS NOT NULL THEN RANK() OVER (PARTITION BY player ORDER BY  trade_pnl ASC) ELSE NULL END::int as losses_rank_alltime,
    CASE WHEN trade_pnl IS NOT NULL THEN RANK() OVER (PARTITION BY player ORDER BY trade_pnl DESC) ELSE NULL END::int as profits_rank_alltime,
    CASE WHEN paperhanded IS NOT NULL THEN RANK() OVER (PARTITION BY player ORDER BY paperhanded DESC) ELSE NULL END::int as paperhand_rank_alltime,
    -- Last 30 days rankings (partitioned by player)
    case WHEN trade_pnl is not null AND sell_timestamp >= CURRENT_DATE - INTERVAL '30 days'  then RANK() OVER (
        PARTITION BY player
        ORDER BY trade_pnl  ASC
    ) ELSE NULL END::int as losses_rank_30d,
    case WHEN trade_pnl is not null AND sell_timestamp >= CURRENT_DATE - INTERVAL '30 days'  then RANK() OVER (
        PARTITION BY player
        ORDER BY trade_pnl  DESC
    ) ELSE NULL END::int as profits_rank_30d,
    CASE  WHEN paperhanded is not null and sell_timestamp >= CURRENT_DATE - INTERVAL '30 days' then RANK() OVER (
        PARTITION BY player
        ORDER BY paperhanded DESC 
    ) ELSE NULL END::int as paperhand_rank_30d,  
    -- Last 14 days rankings (partitioned by player)
case WHEN trade_pnl is not null AND sell_timestamp >= CURRENT_DATE - INTERVAL '14 days'  then RANK() OVER (
        PARTITION BY player
        ORDER BY trade_pnl  ASC
    ) ELSE NULL END::int as losses_rank_14d,
case WHEN trade_pnl is not null AND sell_timestamp >= CURRENT_DATE - INTERVAL '14 days'  then RANK() OVER (
        PARTITION BY player
        ORDER BY trade_pnl  DESC
    ) ELSE NULL END::int as profits_rank_14d,
    CASE  WHEN paperhanded is not null and sell_timestamp >= CURRENT_DATE - INTERVAL '14 days' then RANK() OVER (
        PARTITION BY player
        ORDER BY paperhanded DESC 
    ) ELSE NULL END::int as paperhand_rank_14d
FROM paperhands
ORDER BY sell_timestamp DESC;
"""

conn = get_db_connection()
cursor = conn.cursor()
paperhands_df = pd.read_sql_query(query, conn)
cursor.close()

# Create the three total datasets (aggregate by player) with rank and profile picture
# All-time dataset
total_df_all_time = paperhands_df.groupby('player').agg({
    'paperhanded': 'sum',
    'player_pfp': 'first',
    'player': 'count'
}).rename(columns={'player': 'sell_count'}).reset_index()
total_df_all_time = total_df_all_time.sort_values('paperhanded', ascending=False)
total_df_all_time['rank'] = range(1, len(total_df_all_time) + 1)

# 30-day dataset
df_30d = paperhands_df[paperhands_df['paperhand_rank_30d'].notna()]
total_df_30d = df_30d.groupby('player').agg({
    'paperhanded': 'sum',
    'player_pfp': 'first',
    'player': 'count'
}).rename(columns={'player': 'sell_count'}).reset_index()
total_df_30d = total_df_30d.sort_values('paperhanded', ascending=False)
total_df_30d['rank'] = range(1, len(total_df_30d) + 1)

# 14-day dataset
df_14d = paperhands_df[paperhands_df['paperhand_rank_14d'].notna()]
total_df_14d = df_14d.groupby('player').agg({
    'paperhanded': 'sum',
    'player_pfp': 'first',
    'player': 'count'
}).rename(columns={'player': 'sell_count'}).reset_index()
total_df_14d = total_df_14d.sort_values('paperhanded', ascending=False)
total_df_14d['rank'] = range(1, len(total_df_14d) + 1)

# Create the top 10 by player dataset
top_10_by_player = {}
for player in paperhands_df['player'].unique():
    player_data = paperhands_df[paperhands_df['player'] == player]
    
    # Create a mask for each rank column being <= 10 (nulls will be False)
    rank_columns = [
        'paperhand_rank_alltime', 'losses_rank_alltime', 'profits_rank_alltime',
        'losses_rank_30d', 'profits_rank_30d', 'losses_rank_14d', 
        'profits_rank_14d', 'paperhand_rank_30d', 'paperhand_rank_14d'
    ]
    
    # A row should be included if any non-null rank is <= 10
    player_top_trades = player_data[
        player_data[rank_columns].apply(lambda x: 
            (x <= 10).any() if x.notna().any() else False, 
            axis=1
        )
    ]
    
    player_top_trades = (player_top_trades
                        .sort_values('paperhanded', ascending=False)
                        .replace({pd.NA: None, float('nan'): None})
                        .to_dict('records'))
    top_10_by_player[player] = player_top_trades

# Create a dictionary with all datasets
combined_data = {
    'total_all_time': total_df_all_time.replace({float('nan'): None}).to_dict('records'),
    'total_30d': total_df_30d.replace({float('nan'): None}).to_dict('records'),
    'total_14d': total_df_14d.replace({float('nan'): None}).to_dict('records'),
    'top_10_by_player': {player: [record for record in records] for player, records in top_10_by_player.items()}
}

# Convert to JSON with datetime handling
paperhands_json = json.dumps(combined_data, default=str, indent=4)  # Add indent for pretty printing

# Create directory if it doesn't exist
output_dir = 'pages/data/players'
os.makedirs(output_dir, exist_ok=True)
print(f"Saving to directory: {os.path.abspath(output_dir)}")

# Save to JSON file
output_file = os.path.join(output_dir, 'paperhands.json')
with open(output_file, 'w') as f:
    f.write(paperhands_json)

print(f"File saved to: {os.path.abspath(output_file)}")
print("Total dataset:")
# print(total_df)
print("\nTop 10 by player dataset:")
# print(top_10_by_player)

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
    SELECT DISTINCT buyer_id
    FROM flatten.get_hero_last_trades
    WHERE timestamp >= NOW() - interval '4 weeks'
)
--select count(*) from active_buyers;
,player_sales AS (
    SELECT 
        seller,
        hero_rarity_id,
        hero_handle,
        card_picture,
        seller_id,
        price AS sale_price,
        timestamp AS sale_timestamp
    FROM flatten.get_hero_last_trades
    WHERE 1=1
    --and seller = '0xthemolt'
    AND seller_id IN (SELECT buyer_id FROM active_buyers)
),
latest_prices AS (
    SELECT 
        buyer,
        hero_rarity_id,
        price AS last_sold_price,
        timestamp AS last_trade_timestamp
    FROM flatten.get_hero_last_trades
    WHERE hero_rarity_trade_history_rank = 1
),
base AS (
    SELECT 
        bs.seller as player,
        REPLACE(pd.profile_picture, 'https://pbs.twimg.com/profile_images/', '') as player_pfp,
        bs.hero_handle as hero,
        SUBSTRING(bs.card_picture FROM '/v[12]/(.*)') as hero_card,
        bs.sale_price,
        lp.last_sold_price,
        (lp.last_sold_price - bs.sale_price) as price_diff,
        ROW_NUMBER() OVER (PARTITION BY bs.seller ORDER BY (lp.last_sold_price - bs.sale_price) DESC) as rank_all_time,
        CASE 
            WHEN bs.sale_timestamp >= NOW() - INTERVAL '30 days' 
            THEN ROW_NUMBER() OVER (PARTITION BY bs.seller, (bs.sale_timestamp >= NOW() - INTERVAL '30 days') 
                                   ORDER BY (lp.last_sold_price - bs.sale_price) DESC)
        END as rank_30d,
        CASE 
            WHEN bs.sale_timestamp >= NOW() - INTERVAL '14 days' 
            THEN ROW_NUMBER() OVER (PARTITION BY bs.seller, (bs.sale_timestamp >= NOW() - INTERVAL '14 days') 
                                   ORDER BY (lp.last_sold_price - bs.sale_price) DESC)
        END as rank_14d,
        bs.sale_timestamp,
        CONCAT(lp.buyer,'|',lp.last_trade_timestamp::date) last_sale_string
    FROM player_sales bs
    JOIN latest_prices lp ON bs.hero_rarity_id = lp.hero_rarity_id
    left join flatten.get_player_basic_data pd
    	on bs.seller_id = pd.player_id
    WHERE lp.last_sold_price > bs.sale_price
    AND lp.last_trade_timestamp > bs.sale_timestamp
    ORDER BY price_diff desc
)
SELECT * FROM base;
"""

conn = get_db_connection()
cursor = conn.cursor()
paperhands_df = pd.read_sql_query(query, conn)
cursor.close()

# Create the three total datasets (aggregate by player) with rank and profile picture
# All-time dataset
total_df_all_time = paperhands_df.groupby('player').agg({
    'price_diff': 'sum',
    'player_pfp': 'first',
    'player': 'count'
}).rename(columns={'player': 'sell_count'}).reset_index()
total_df_all_time = total_df_all_time.sort_values('price_diff', ascending=False).head(50)
total_df_all_time['rank'] = range(1, len(total_df_all_time) + 1)

# 30-day dataset
df_30d = paperhands_df[paperhands_df['rank_30d'].notna()]  # Filter for trades within 30 days
total_df_30d = df_30d.groupby('player').agg({
    'price_diff': 'sum',
    'player_pfp': 'first',
    'player': 'count'
}).rename(columns={'player': 'sell_count'}).reset_index()
total_df_30d = total_df_30d.sort_values('price_diff', ascending=False).head(50)
total_df_30d['rank'] = range(1, len(total_df_30d) + 1)

# 14-day dataset
df_14d = paperhands_df[paperhands_df['rank_14d'].notna()]  # Filter for trades within 14 days
total_df_14d = df_14d.groupby('player').agg({
    'price_diff': 'sum',
    'player_pfp': 'first',
    'player': 'count'
}).rename(columns={'player': 'sell_count'}).reset_index()
total_df_14d = total_df_14d.sort_values('price_diff', ascending=False).head(50)
total_df_14d['rank'] = range(1, len(total_df_14d) + 1)

# Create the top 10 by player dataset
top_10_by_player = {}
for player in paperhands_df['player'].unique():
    player_data = paperhands_df[paperhands_df['player'] == player]
    # Get top 10 records and drop NaN columns
    player_top_10 = (player_data.nsmallest(10, 'rank_all_time')
                    .dropna(axis=1)  # This will remove columns that are all NaN
                    .to_dict('records'))
    top_10_by_player[player] = player_top_10

# Create a dictionary with all datasets
combined_data = {
    'total_all_time': total_df_all_time.to_dict('records'),
    'total_30d': total_df_30d.to_dict('records'),
    'total_14d': total_df_14d.to_dict('records'),
    'top_10_by_player': top_10_by_player
}

# Convert to JcSON with datetime handling
paperhands_json = json.dumps(combined_data, default=str)

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

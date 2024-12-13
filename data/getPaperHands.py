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

query = """WITH buyer_sales AS (
    SELECT 
        buyer,
        hero_rarity_id,
        hero_handle,
        card_picture,
        buyer_id,
        price AS sale_price,
        timestamp AS sale_timestamp
    FROM flatten.get_hero_last_trades
    WHERE buyer = '0xthemolt'
),
latest_prices AS (
    SELECT 
        hero_rarity_id,
        price AS last_sold_price,
        timestamp AS last_trade_timestamp
    FROM flatten.get_hero_last_trades
    WHERE hero_rarity_trade_history_rank = 1
)
SELECT 
    bs.buyer as player,
    --bs.hero_rarity_id,
    bs.hero_handle as hero,
    SUBSTRING(bs.card_picture FROM '/v[12]/.*') as hero_card,
    --bs.card_picture as hero_card,
    --bs.buyer_id,
    bs.sale_price,
    lp.last_sold_price,
    (lp.last_sold_price - bs.sale_price) as price_difference,
    ROW_NUMBER() OVER (PARTITION BY bs.buyer ORDER BY (lp.last_sold_price - bs.sale_price) DESC) as rank,
    bs.sale_timestamp
    --lp.last_trade_timestamp
FROM buyer_sales bs
JOIN latest_prices lp ON bs.hero_rarity_id = lp.hero_rarity_id
WHERE lp.last_sold_price > bs.sale_price
    AND lp.last_trade_timestamp > bs.sale_timestamp
ORDER BY price_difference DESC;
"""

conn = get_db_connection()
cursor = conn.cursor()
paperhands_df = pd.read_sql_query(query, conn)
cursor.close()

# Convert DataFrame to JSON format
paperhands_json = paperhands_df.to_json(orient='records')

# Create directory if it doesn't exist
output_dir = 'pages/data/players'
os.makedirs(output_dir, exist_ok=True)
print(f"Saving to directory: {os.path.abspath(output_dir)}")

# Save to JSON file
output_file = os.path.join(output_dir, 'paperhands.json')
with open(output_file, 'w') as f:
    f.write(paperhands_json)

print(f"File saved to: {os.path.abspath(output_file)}")
print(paperhands_df)

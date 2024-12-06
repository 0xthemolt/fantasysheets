import psycopg2
from psycopg2 import pool
import json
import os
from datetime import datetime
import pandas as pd
from contextlib import contextmanager

# Database configuration - Should be moved to a config file or env variables
DB_CONFIGS = {
    'main': {
        'dbname': "0xthemolt",
        'user': "postgres",
        'password': "admin",
        'host': "localhost",
        'port': "5432"
    },
    'prices': {
        'dbname': "fantasysheets",
        'user': "postgres",
        'password': "WIKrjPIYtqCWApMIXculsqbMIQcGotEg",
        'host': "viaduct.proxy.rlwy.net",
        'port': "38391"
    }
}

# Connection pool management
@contextmanager
def get_db_connection(db_type='main'):
    conn = psycopg2.connect(**DB_CONFIGS[db_type])
    try:
        yield conn
    finally:
        conn.close()

def fetch_dataframe(query, db_type='main'):
    with get_db_connection(db_type) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    return df

trades_query = f"""
select hero_id,hero_handle,rarity,card_picture,timestamp,buyer,seller,price
from flatten.get_hero_last_trades 
where 1=1
--and hero_handle = 'CoinGurruu'
and buyer <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
and timestamp >= NOW() at time zone 'UTC' - interval '45 days'
"""

prices_query = f"""SELECT ghwss.hero_id,ghwss.hero_handle, prices.rarity,prices.bid,prices.floor
FROM flatten.vwhero_stats_bids  prices
left join flatten.herohandlehistory handles
on prices.hero = handles.hero_handle
left join flatten.get_heros_with_stats_snapshot ghwss 
on handles.current_hero_handle  = ghwss.hero_handle 
and ghwss.is_deleted  = 0
and ghwss.snapshot_rank  = 1
and ghwss.start_datetime  >= NOW() - interval '5 days'
where rarity in ('rare','common')
order by 1 asc
"""


def process_hero_trades():
    # Fetch trades and prices data
    trades_df = fetch_dataframe(trades_query, 'main')
    prices_df = fetch_dataframe(prices_query, 'prices')
    # Ensure timestamp is formatted correctly
    if not trades_df.empty:
        trades_df['timestamp'] = trades_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        directory = "pages/data/heroes"
        os.makedirs(directory, exist_ok=True)
        
        for hero_handle in trades_df['hero_handle'].unique():
            # Filter trades for current hero
            hero_trades = trades_df[trades_df['hero_handle'] == hero_handle]
            
            # Get matching price data for the hero
            hero_prices = prices_df[prices_df['hero_handle'] == hero_handle]
            
            # Create combined dictionary
            hero_data = {
                'trades': json.loads(hero_trades.to_json(orient='records')),
                'prices': json.loads(hero_prices.to_json(orient='records')) if not hero_prices.empty else None
            }
            
            # Save to JSON file
            json_filename = os.path.join(directory, f"{hero_handle}_trades.json")
            with open(json_filename, 'w') as f:
                json.dump(hero_data, f, indent=2)
            
            print(f"JSON file saved for {hero_handle} at: {os.path.abspath(json_filename)}")

if __name__ == "__main__":
    process_hero_trades()


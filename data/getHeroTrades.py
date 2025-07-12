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
        'dbname' : "postgres",
        'user' : "postgres.hhcuqhvmzwmehdsaamhn",
        'password' : "Wafj2DCrI6Yjbe4I",
        'host' : "aws-0-us-west-1.pooler.supabase.com",
        'port' : "5432"
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
select hero_id,hero_handle,rarity,card_picture,timestamp,buyer,seller,price,hero_rarity_trade_history_rank
from flatten.get_hero_last_trades 
where 1=1
--and hero_handle = 'CoinGurruu'
and buyer <> '0xCA6a9B8B9a2cb3aDa161bAD701Ada93e79a12841'
and timestamp >= NOW() at time zone 'UTC' - interval '90 days'
"""

prices_query = f"""SELECT prices.hero_id,prices.hero_handle, prices.hero_rarity as rarity,prices.bid_price as bid,prices.floor_price as floor
    FROM flatten.marketplace_basic  prices
    where hero_rarity in ('rare','common')
    order by 1 asc
"""

last_trades_query = """
  SELECT hero_handle, card_rarity as rarity, 
       price as last_price,
       trade_timestamp  as last_trade_time
FROM flatten.hero_Trades
WHERE flatten.hero_trades.hero_rarity_id_history_rank  = 1
"""

sell_orders_query = """
  with heros_five_listings as (select hero_handle,rarity ,1 has_five from flatten.sell_orders_detail group by 1,2 having max(flatten.sell_orders_detail.hero_rarity_sell_order_rnk) >= 5)
select base.hero_handle,base.rarity,count(*) as sell_orders
,avg(case  when hero_rarity_sell_order_rnk <= 5 and has_five = 1 then price else null end) buy_5_avg
,suM(case  when hero_rarity_sell_order_rnk <= 5 and has_five = 1  then price else 0 end) buy_5_sum 
from flatten.sell_orders_detail base 
left join heros_five_listings five 
	on base.hero_handle = five.hero_handle
	and base.rarity = five.rarity
group by 1,2
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

def process_marketplace():
    # Fetch trades and prices data
    trades_df = fetch_dataframe(trades_query, 'main')
    prices_df = fetch_dataframe(prices_query, 'prices')
    sell_orders_df = fetch_dataframe(sell_orders_query, 'prices')

    if not trades_df.empty:
        current_time = pd.Timestamp.now()
        
        # Define timeframes in hours
        timeframes = {
            '6h': 6,
            '24h': 24,
            '3d': 24 * 3,
            '7d': 24 * 7
        }

        # Calculate base stats as before
        market_stats = trades_df.groupby(['hero_handle', 'rarity']).agg({
            'hero_id': 'first',
            'card_picture': 'first',
            'timestamp': lambda x: (current_time - pd.to_datetime(x.max())).total_seconds() / 3600,
            'hero_handle': 'count',
            'buyer': 'nunique',
            'price': 'sum'
        }).rename(columns={
            'hero_handle': 'trades',
            'buyer': 'buyers',
            'timestamp': 'hours_since_last_trade',
            'price': 'volume'
        }).reset_index()

        # Count before first merge
        print("Count before first merge:", market_stats[market_stats['hero_handle'] == 'zagabond'].shape[0])

        # Add sell orders data - merge after the initial market_stats calculation
        market_stats = market_stats.merge(
            sell_orders_df[['hero_handle', 'rarity', 'sell_orders', 'buy_5_avg', 'buy_5_sum']],
            on=['hero_handle', 'rarity'],
            how='left'
        )

        # Count after first merge
        print("Count after first merge:", market_stats[market_stats['hero_handle'] == 'zagabond'].shape[0])

        # Merge with prices_df to get seven_day_fantasy_score before timeframe calculations
        market_stats = market_stats.merge(
            prices_df[['hero_handle', 'rarity']],
            on=['hero_handle', 'rarity'],
            how='left'
        )

        # Count after second merge
        print("Count after second merge:", market_stats[market_stats['hero_handle'] == 'zagabond'].shape[0])

        # Add timeframe_stats as a string column initially
        market_stats['timeframe_stats'] = None

        # Calculate timeframe metrics
        for hero_handle in trades_df['hero_handle'].unique():
            for rarity in trades_df[trades_df['hero_handle'] == hero_handle]['rarity'].unique():
                hero_trades = trades_df[
                    (trades_df['hero_handle'] == hero_handle) & 
                    (trades_df['rarity'] == rarity)
                ]
                
                timeframe_stats = []
                for period, hours in timeframes.items():
                    cutoff = current_time - pd.Timedelta(hours=hours)
                    period_trades = hero_trades[pd.to_datetime(hero_trades['timestamp']) >= cutoff]
                    
                    if not period_trades.empty:
                        stats = {
                            'timeframe': period,
                            'volume': float(period_trades['price'].sum()),
                            'avg_price': float(period_trades['price'].mean()),
                            'med_price': float(period_trades['price'].median()),
                            'min_price': float(period_trades['price'].min()),
                            'max_price': float(period_trades['price'].max()),
                            'buyers': len(period_trades['buyer'].unique())
                        }
                    else:
                        stats = {
                            'timeframe': period,
                            'volume': 0,
                            'avg_price': 0,
                            'med_price': 0,
                            'min_price': 0,
                            'max_price': 0,
                            'buyers': 0
                        }
                    timeframe_stats.append(stats)
                
                # Add timeframe_stats to market_stats
                mask = (market_stats['hero_handle'] == hero_handle) & (market_stats['rarity'] == rarity)
                market_stats.at[mask.idxmax(), 'timeframe_stats'] = timeframe_stats

        # Merge with prices data and last trade
        last_trades = fetch_dataframe(last_trades_query, 'prices')
        market_data = pd.merge(
            market_stats,
            prices_df[['hero_handle', 'rarity', 'floor', 'bid']],
            on=['hero_handle', 'rarity'],
            how='left'
        ).merge(
            last_trades,
            on=['hero_handle', 'rarity'],
            how='left'
        )

        # Convert to dictionary/JSON format
        market_json = json.loads(market_data.to_json(orient='records'))

        # Save to JSON file
        directory = "pages/data/marketplace"
        os.makedirs(directory, exist_ok=True)
        
        json_filename = os.path.join(directory, "marketplace.json")
        with open(json_filename, 'w') as f:
            json.dump(market_json, f, indent=2)
        
        print(f"Marketplace JSON file saved at: {os.path.abspath(json_filename)}")

if __name__ == "__main__":
    process_hero_trades()
    process_marketplace()


import psycopg2
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



@contextmanager
def get_db_connection(db_type='main'):
    """Context manager for database connections"""
    config = DB_CONFIGS[db_type]
    conn = psycopg2.connect(**config)
    try:
        yield conn
    finally:
        conn.close()

# Replace the direct connection code with context managers
with get_db_connection('main') as conn:
    cursor = conn.cursor()
    
    # Get star ranges
    star_ranges_query = f"""CALL master.update_star_ranges();  
    select * from master.star_ranges
    """
    cursor.execute(star_ranges_query)
    star_ranges_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    print("\n=== Star Ranges DataFrame ===")
    print(star_ranges_df)
    print(f"Shape: {star_ranges_df.shape}")
    
    # Get hero stats
    hero_stats_query = f"""
   with l3_main as (
    select ghwst.hero_id , PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY ghwst.fantasy_Score) l3_main_median  
    from flatten.get_heros_with_stats_tournament ghwst 
    join flatten.get_tournaments gt 
        on ghwst.tournament_id  = gt.tournament_id 
    where 1=1
    --ghwst.hero_handle  = '0xgaut'
    and gt.tournament_seq_nbr  <= 4 
    and gt.tournament_status = 'finished'
    and gt.league  = 'Elite'
    group by 1
    )
    ,last_main as ( 
    select ghwst.hero_id , ghwst.fantasy_Score last_main  
    from flatten.get_heros_with_stats_tournament ghwst 
    join flatten.get_tournaments gt 
        on ghwst.tournament_id  = gt.tournament_id 
    where 1=1
    --ghwst.hero_handle  = '0xgaut'
    and gt.tournament_seq_nbr  in (select min(tournament_seq_nbr) from flatten.get_tournaments where tournament_status in ('live','finished') and league = 'Elite')
    and gt.league = 'Elite'
    )
    select ghss.hero_handle,ghss.hero_name,ghss.hero_id,ghss.hero_pfp_image_url as hero_image_url
    ,ghss.seven_day_fantasy_score  as seven_day_score
    ,gcfs.hero_stars as current_stars
    ,projected_star.hero_stars as projected_stars
    ,projected_star.hero_stars - gcfs.hero_stars  as projected_stars_diff
    ,current_star.top_range
    ,ghss.seven_day_fantasy_score
    ,l3_main.l3_main_median
    ,last_main.last_main
    ,sup.legendary_cards 
    ,sup.epic_cards 
    ,sup.rare_cards 
    ,sup.common_cards 
    ,sup.aggregate_cards 
    from flatten.GET_HEROS_WITH_STATS_SNAPSHOT ghss
    left join flatten.get_supply_per_hero_id sup
    	on ghss.hero_id = sup.hero_id 
    	and sup.snapshot_rank  = 1
    left join flatten.get_cards_flags_stars gcfs 
        on ghss.hero_id = gcfs.hero_id 
        and gcfs.snapshot_rank = 1
    left join master.star_ranges current_star
        on gcfs.hero_stars = current_star.stars 
    left join master.hero_stars  projected_star
        on ghss.hero_id  = projected_star.hero_id
    left join l3_main
        on ghss.hero_id  = l3_main.hero_id
    left join last_main
        on ghss.hero_id  = last_main.hero_id
    where ghss.is_deleted  = 0
    and ghss.snapshot_rank = 1
    and ghss.start_datetime >= '2024-10-01'
    order by 3 desc
    """
    cursor.execute(hero_stats_query)
    hero_stats_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    print("\n=== Hero Stats DataFrame ===")
    print(hero_stats_df)
    print(f"Shape: {hero_stats_df.shape}")

# Use different connection for prices if needed
with get_db_connection('prices') as conn:
    cursor = conn.cursor()
    prices_query = f"""SELECT prices.hero_id,prices.hero_handle, prices.hero_rarity as rarity,prices.bid_price as bid,prices.floor_price as floor
    FROM flatten.marketplace_basic  prices
    where hero_rarity in ('rare','common')
    order by 1 asc
    """
    cursor.execute(prices_query)
    prices_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    print("\n=== Prices DataFrame ===")
    print(prices_df)
    print(f"Shape: {prices_df.shape}")

# Filter prices_df for each rarity before merging
common_prices = prices_df[prices_df['rarity'] == 'common'][['hero_id', 'floor']].drop_duplicates('hero_id')
rare_prices = prices_df[prices_df['rarity'] == 'rare'][['hero_id', 'floor']].drop_duplicates('hero_id')

# Merge hero_stats_df with prices_df for both rarities
final_merged_df = (hero_stats_df
    .merge(common_prices, on='hero_id', how='left', suffixes=('', '_common'))
    .rename(columns={'floor': 'common_floor'})
    .merge(rare_prices, on='hero_id', how='left', suffixes=('', '_rare'))
    .rename(columns={'floor': 'rare_floor'})
)

# Calculate score_per_eth
final_merged_df['score_per_eth'] = (
    ((final_merged_df['seven_day_fantasy_score'].astype(float) + final_merged_df['last_main'].astype(float)) / 2 / 
    final_merged_df['common_floor'].astype(float).replace(0, float('inf')))
    / 100
).where(
    ((final_merged_df['seven_day_fantasy_score'] != 0) | (final_merged_df['last_main'] != 0)) & 
    (final_merged_df['common_floor'].notna()) & 
    (final_merged_df['common_floor'] != 0), 
    0
)

# Add debug print for final merged DataFrame
print("\n=== Final Merged DataFrame ===")
print(final_merged_df)
print(f"Shape: {final_merged_df.shape}")

# Create JSON structure and save to file
output_data = {
    "metadata": json.loads(star_ranges_df.to_json(orient='records', date_format='iso')),
    "heroes": json.loads(final_merged_df.to_json(orient='records', date_format='iso'))
}

# Save to JSON file
output_path = 'pages/hero_stats.json'
print(f"Saving data to: {os.path.abspath(output_path)}")
with open(output_path, 'w') as f:
    json.dump(output_data, f, indent=2)
print(f"✅ File successfully saved to: {os.path.abspath(output_path)}")

# Close database connections
cursor.close()
conn.close()

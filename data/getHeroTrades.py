import psycopg2
import json
import os
from datetime import datetime
import pandas as pd


conn = psycopg2.connect(
    dbname="0xthemolt",
    user="postgres",
    password="admin",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

trades_query = f"""
select hero_id,hero_handle,rarity,card_picture,timestamp,buyer,seller,price
from flatten.get_hero_last_trades 
where 1=1
--and hero_handle = 'CoinGurruu'
and timestamp >= NOW() at time zone 'UTC' - interval '10 days'
"""

cursor.execute(trades_query)
trades_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])



def get_price_db_connection():
    return psycopg2.connect(
        dbname="fantasysheets",
        user="postgres",
        password="WIKrjPIYtqCWApMIXculsqbMIQcGotEg",
        host="viaduct.proxy.rlwy.net",
        port="38391"
    )


# Convert DataFrame to JSON and save to file
if not trades_df.empty:
    # Convert timestamp to desired format
    trades_df['timestamp'] = trades_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get unique hero handles
    unique_heroes = trades_df['hero_handle'].unique()
    
    # Create the directory path
    directory = "pages/data/heroes"
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
    
    # Loop through each unique hero
    for hero_handle in unique_heroes:
        # Filter DataFrame for current hero
        hero_trades = trades_df[trades_df['hero_handle'] == hero_handle]
        
        # Create json filename for this hero
        json_filename = os.path.join(directory, f"{hero_handle}_trades.json")
        
        # Convert DataFrame to JSON format
        trades_json = hero_trades.to_json(orient='records')
        
        # Write to JSON file
        with open(json_filename, 'w') as f:
            f.write(trades_json)
        
        # Print the full file path
        print(f"JSON file saved for {hero_handle} at: {os.path.abspath(json_filename)}")


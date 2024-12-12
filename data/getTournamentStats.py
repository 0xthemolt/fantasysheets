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

# First query into league_decks_df
conn = get_db_connection()
cursor = conn.cursor()
league_decks_query = f"""select 
    concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
    gt.tournament_unique_key,
    substring(gt.tournament_unique_key from position(' ' in gt.tournament_unique_key) + 1) AS tournament_number,
    league,
    COUNT(*) deck_count,
    COUNT(distinct gtpp.player_id) player_count
from
    flatten.get_tournaments gt
join flatten.get_tournament_past_players gtpp
    on gt.tournament_id = gtpp.tournament_id
where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
group by 1,2,3,4"""
league_decks_df = pd.read_sql_query(league_decks_query, conn)
cursor.close()

total_players_query = f"""select 
    concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
    gt.tournament_unique_key,
    substring(gt.tournament_unique_key from position(' ' in gt.tournament_unique_key) + 1) AS tournament_number,
    COUNT(distinct gtpp.player_id) player_count
from
    flatten.get_tournaments gt
join flatten.get_tournament_past_players gtpp
    on gt.tournament_id = gtpp.tournament_id
where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
group by 1,2,3"""
total_players_df = pd.read_sql_query(total_players_query, conn)
cursor.close()


# Second query into card_stars_df
conn = get_db_connection()
cursor = conn.cursor()
card_stars_query = f"""select concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
 gt.tournament_unique_key,
    coalesce(t.hero_stars,1) hero_stars,
    count(*) card_count,
    count(distinct t.player_id) player_count
from agg.tournamentownership t 
join   flatten.get_tournaments gt
    on t.tournament_id  = gt.tournament_id 
    where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
group by 1,2,3"""
card_stars_df = pd.read_sql_query(card_stars_query, conn)
cursor.close()

# Create the JSON structure
tournaments_data = {}

# Process league_decks_df
for _, row in league_decks_df.iterrows():
    tournament_key = row['tournament']
    if tournament_key not in tournaments_data:
        tournaments_data[tournament_key] = {
            'tournament_unique_key': row['tournament_unique_key'],
            'leagues': [],
            'stars': []
        }
    tournaments_data[tournament_key]['leagues'].append({
        'league': row['league'],
        'deck_count': int(row['deck_count']),
        'player_count': int(row['player_count'])
    })

# Process total_players_df
for _, row in total_players_df.iterrows():
    tournament_key = row['tournament']
    if tournament_key in tournaments_data:
        tournaments_data[tournament_key]['total_player_count'] = int(row['player_count'])

# Process card_stars_df
for _, row in card_stars_df.iterrows():
    tournament_key = row['tournament']
    if tournament_key in tournaments_data:
        tournaments_data[tournament_key]['stars'].append({
            'hero_stars': int(row['hero_stars']),
            'card_count': int(row['card_count'])
        })

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)

# Write to JSON file using absolute path
output_file = os.path.join(output_dir, 'tournaments_stats.json')
with open(output_file, 'w') as f:
    json.dump(tournaments_data, f, indent=4)

# Print the full path
print(f"Writing data to: {output_file}")

# Close the final connection
conn.close()



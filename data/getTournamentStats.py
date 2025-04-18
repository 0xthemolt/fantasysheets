import psycopg2
import json
import os
from datetime import datetime
import pandas as pd

def supabase_db_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres.hhcuqhvmzwmehdsaamhn",
        password="$&roct8&rgp4NE",
        host="aws-0-us-west-1.pooler.supabase.com",
        port="5432"
    )

# postgresql://postgres.hhcuqhvmzwmehdsaamhn:$&roct8&rgp4NE@aws-0-us-west-1.pooler.supabase.com:5432/postgres

# First query into league_decks_df
conn = supabase_db_connection()
cursor = conn.cursor()
league_decks_query = f"""select 
    concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
    gt.start_timestamp,
    gt.tournament_unique_key,
    substring(gt.tournament_unique_key from position(' ' in gt.tournament_unique_key) + 1) AS tournament_number,
    gt.league,
    max(gt.registered_decks) deck_count,
    max(gt.player_count) player_count
from
    flatten.get_tournaments gt
where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
    or gt.tournament_status = 'not started'
group by 1,2,3,4,5
order by gt.start_timestamp asc"""
league_decks_df = pd.read_sql_query(league_decks_query, conn)
cursor.close()

total_players_query = f"""select 
    concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
    gt.start_timestamp,
    gt.tournament_unique_key,
    substring(gt.tournament_unique_key from position(' ' in gt.tournament_unique_key) + 1) AS tournament_number,
    COUNT(distinct gtpp.player_id) player_count
from
    flatten.get_tournaments gt
join flatten.tournament_players gtpp
    on gt.tournament_id = gtpp.tournament_id
where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
group by 1,2,3,4
order by gt.start_timestamp asc"""
total_players_df = pd.read_sql_query(total_players_query, conn)
cursor.close()


card_stars_query = f"""select concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
gt.start_timestamp,
 gt.tournament_unique_key,
    coalesce(t.hero_stars,1) hero_stars,
    count(*) card_count
from agg.tournamentownership t 
join   flatten.get_tournaments gt
    on t.tournament_id  = gt.tournament_id 
    where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
group by 1,2,3,4
order by gt.start_timestamp asc"""
card_stars_df = pd.read_sql_query(card_stars_query, conn)
cursor.close()


rarity_query = f"""select concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
gt.start_timestamp,
 gt.tournament_unique_key,
    t.hero_rarity,
    count(*) card_count
from agg.tournamentownership t 
join   flatten.get_tournaments gt
    on t.tournament_id  = gt.tournament_id 
    where gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
    and gt.tournament_number not in (45)
group by 1,2,3,4
order by gt.start_timestamp asc"""
card_rarity_df = pd.read_sql_query(rarity_query, conn)
cursor.close()

conn_two = supabase_db_connection()
cursor_two = conn_two.cursor()
tournament_views_query = f"""with base as (
select ghwst.tournament_unique_key
,ROUND(EXTRACT(EPOCH FROM (ghwst.db_updated_utc -  gt.start_timestamp at time zone 'UTC')) / 3600,0) AS hours_since_start
,gt.start_timestamp  at time zone 'UTC'
,ghwst.db_updated_utc
,sum(views) views
,sum(case when score = 0 then 1 else 0 end) score_0_count
from flatten.hero_stats_Tournament ghwst 
join flatten.get_tournaments gt  
	on ghwst.tournament_id = gt.tournament_id
where 1=1
--hero_handle = 'CryptoKaleo'
--and ghwst.tournament_unique_key  = 'Main 33'
and gt.tournament_status <> 'not started'
and gt.tournament_seq_nbr <= 6
group by 1,2,3,4
)
select tournament_unique_key
,hours_since_start
,max(views) views
,max(score_0_count) score_0_count
from base
where hours_since_Start <= (24*3)
group by 1,2
order by 1,2"""
tournament_views_df = pd.read_sql_query(tournament_views_query, conn_two)
print(f"Number of records in tournament_views_df: {len(tournament_views_df)}")
cursor_two.close()

# Create the JSON structure
tournaments_data = {}

# Process league_decks_df
for _, row in league_decks_df.iterrows():
    tournament_key = row['tournament']
    if tournament_key not in tournaments_data:
        tournaments_data[tournament_key] = {
            'tournament_unique_key': row['tournament_unique_key'],
            'leagues': [],
            'stars': [],
            'rarity': []
        }
    tournaments_data[tournament_key]['leagues'].append({
        'league': row['league'],
        'deck_count': int(row['deck_count']),
        'player_count': int(row['player_count']) if not pd.isna(row['player_count']) else None
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

# Process card_rarity_df
for _, row in card_rarity_df.iterrows():
    tournament_key = row['tournament']
    if tournament_key in tournaments_data:
        tournaments_data[tournament_key]['rarity'].append({
            'hero_rarity': row['hero_rarity'],
            'card_count': int(row['card_count'])
        })
# Process tournament views data
tournament_views_data = {}
print("Debug: Number of rows in tournament_views_df:", len(tournament_views_df))
for _, row in tournament_views_df.iterrows():
    tournament_key = row['tournament_unique_key']
    hours = int(row['hours_since_start'])
    # print(f"Debug: Processing tournament {tournament_key}, hours: {row['hours_since_start']}, views: {row['views']}")
    
    if tournament_key not in tournament_views_data:
        tournament_views_data[tournament_key] = {}
    
    # If we already have this hour and it's not a duplicate, skip it
    # If it's a duplicate, we'll overwrite with the latest data
    tournament_views_data[tournament_key][hours] = {
        'hours_since_start': hours,
        'views': int(row['views']),
        'score_0_count': int(row['score_0_count'])
    }

# Convert the hour dictionaries back to lists for JSON serialization
for tournament_key in tournament_views_data:
    tournament_views_data[tournament_key] = list(tournament_views_data[tournament_key].values())

# Get the absolute path for the output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'tournaments')

# Ensure the tournaments directory exists
os.makedirs(output_dir, exist_ok=True)

# Write main tournaments data to JSON
output_file = os.path.join(output_dir, 'tournaments_stats.json')
with open(output_file, 'w') as f:
    json.dump(tournaments_data, f, indent=4)

print(f"Writing data to: {output_file}")


# Write tournament views to separate JSON file
output_views_file = os.path.join(output_dir, 'tournaments_stats_view_growth.json')
with open(output_views_file, 'w') as f:
    json.dump(tournament_views_data, f, indent=4)

print(f"Writing tournament views data to: {output_views_file}")

# Close the final connection
conn.close()



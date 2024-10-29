import psycopg2
import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable, viridis
from decimal import Decimal

# Load configuration from config.json
with open('C:/fantasy_top_analysis/pages/config.json', 'r') as config_file:
    config = json.load(config_file)

# PLACEHOLDER_IMAGE = config['placeholder_image']    "placeholder_image": "https://pbs.twimg.com/profile_images/1754590022664101888/geh_HFDq_400x400.jpg",
TOURNAMENT_NUMBER = config['tournament_number']
LEAGUE_IMAGES = config['league_images']
REWARD_IMAGES = config['reward_images']

def get_heroes_data():
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname="0xthemolt",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

    # Query the database
    query = f"""
            with tournament_base as (
            select *
            from flatten.get_heros_with_stats_tournament
            where tournament_unique_key  = 'Main 23' 
            and tournament_league_unique_key not like '%Reverse%' 
            )
            ,current_scores as (
            select *,PERCENT_RANK() OVER (ORDER BY seven_day_rank asc) AS percentile
            from flatten.GET_HEROS_WITH_STATS_SNAPSHOT
            where is_deleted = 0
            and snapshot_rank = 1
            and db_updated_cst >= '2024-10-10'
            )
            ,base2 as (
            SELECT 
            seven_day_fantasy_score fantasy_score,
            CASE
                WHEN percentile <= 0.125 THEN 8
                WHEN percentile <= 0.25 THEN 7
                WHEN percentile <= 0.375 THEN 6
                WHEN percentile <= 0.50 THEN 5
                WHEN percentile <= 0.625 THEN 4
                WHEN percentile <= 0.75 THEN 3
                WHEN percentile <= 0.875 THEN 2
                ELSE 1
            END AS star_rating
            FROM current_scores
            ORDER BY fantasy_score desc
            )
            ,star_range as (
            select star_rating
            ,min(fantasy_score) min_score_range
            ,max(fantasy_score) max_score_range
            ,PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY fantasy_score)  midpoint
            ,max(fantasy_score) - min(fantasy_score)
            from base2
            group by 1
            )
            ,current_hero_star as (
            SELECT ghst.hero_id, ghst.fantasy_score,MAX(sr.star_rating) star_rating
            FROM tournament_base ghst
            JOIN star_range sr 
            ON ghst.fantasy_score >= sr.min_score_range
            GROUP BY 1,2
            )
            , player_sample AS (
                SELECT tournament_unique_key
                ,COUNT(DISTINCT tournament_player_deck_id) AS total_decks
                ,COUNT(DISTINCT tournament_player_deck_id)*5 AS total_cards
                FROM agg.TournamentOwnership
                WHERE 1=1 and tournament_league_unique_key <> 'Reverse Score 2'
                group by tournament_unique_key
            )
            SELECT 
                a.hero_handle,  --0
                hero_stars hero_stars,  --1
                current_hero_star.star_rating as current_hero_stars,
                coalesce(ghwss.hero_pfp_image_url  , 'https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v1/neutral/' || a.hero_handle || '.png')  as hero_pfp_url,  --2
            -- 'https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v1/neutral/' || a.hero_handle || '.png' hero_pfp_url,
                COUNT(*) AS card_usage_count, --3
                COUNT(*)::NUMERIC/MAX(total_cards) AS card_utilization,  --4
                MAX(ROUND(COALESCE(ghst.fantasy_score,0), 0)) AS hero_fantasy_score,  --5
                MAX(ROUND(COALESCE(ghst.reach,0), 0)) AS reach,  --6
                MAX(ROUND(COALESCE(ghst.views,0), 0)) AS views,  --7
                MAX(ROUND(COALESCE(ghst.tweet_count,0), 0)) AS tweets, --8
                MAX(total_decks) AS total_decks, --10
                MAX(total_cards) as total_cards, --11
                MIN(a.db_updated_cst)::timestamp AS score_timestamp  --12
            FROM agg.TournamentOwnership a
            JOIN tournament_base ghst
                on a.hero_id = ghst.hero_id
                and a.tournament_id = ghst.tournament_id
            left join current_hero_star
                on a.hero_id = current_hero_star.hero_id
            LEFT JOIN flatten.get_heros_with_stats_snapshot ghwss 
                ON a.hero_id = ghwss.hero_id 
                AND ghwss.snapshot_rank = 1 
            CROSS JOIN player_sample
            WHERE 1=1
            and a.hero_handle not IN ('satsdart','delucinator')
            and a.tournament_unique_key = player_sample.tournament_unique_key
            GROUP BY 1, 2, 3, 4
            ORDER BY CAST(COUNT(*) AS FLOAT)/100 DESC
    """
    df_heroes = pd.read_sql(query, conn)
    
    # Close the connection
    conn.close()
    
    # After fetching the heroes data, sort by hero_fantasy_score in descending order
    df_heroes = df_heroes.sort_values(by='hero_fantasy_score', ascending=False)

    # Add a rank column based on total_utilization, skipping identical values
    df_heroes['rank'] = df_heroes['hero_fantasy_score'].rank(method='dense', ascending=False).astype(int)

    # Calculate the latest timestamp and time difference
    latest_score_timestamp = max(df_heroes['score_timestamp'])
    latest_score_timestamp = df_heroes['score_timestamp'].max().strftime("%Y-%m-%d %H:%M")

    return df_heroes, latest_score_timestamp


def format_percentage(value):
    """Helper function to format utilization percentages"""
    if pd.isna(value):
        return "0%"
    return f"{value*100:.1f}%"

def generate_html(df_heroes, latest_score_timestamp):
    # Calculate min and max scores for color scaling
    min_score = df_heroes['hero_fantasy_score'].min()
    max_score = df_heroes['hero_fantasy_score'].max()
    
    total_heroes = len(df_heroes)
    total_decks = df_heroes['total_decks'].iloc[0]
    total_cards = df_heroes['total_cards'].iloc[0]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hero Score Center</title>
        <link rel="stylesheet" href="./styles.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    </head>
    <body>
        <div class="title-container">
            <h1>
                <a href="home.html" class="home-link">
                    <i class="fas fa-home"></i>
                </a>
                Hero Score Center
            </h1>
            <div class="tournament-badge">Main {TOURNAMENT_NUMBER}</div>
        </div>
        <div id="search-container">
            <input type="text" id="hero-search-box" class="search-box" placeholder="Search Heroes">
        </div>
        <div class="small-text">
            <span>Heroes: {total_heroes} &nbsp;|&nbsp; Decks: {total_decks:,} &nbsp;|&nbsp; Cards: {total_cards:,} &nbsp;|&nbsp; Updated: {latest_score_timestamp} UTC</span>
        </div>
        <table id="heroesTable">
            <tr>
                <th>Rank</th>
                <th style="text-align: left;">Hero</th>
                <th class="rank-columns" data-sort="hero_fantasy_score">Score</th>
                <th class="rank-columns" data-sort="card_utilization">Utilization</th>
                <th>Stars</th>
                <th>Reach</th>
                <th>Views</th>
                <th>Tweets</th>
            </tr>
    """

    # Add rows for each hero
    for _, row in df_heroes.iterrows():
        # Calculate color based on fantasy score
        score_percentage = (row['hero_fantasy_score'] - min_score) / (max_score - min_score)
        score_color = f"hsl({int(120 * score_percentage)}, 70%, 50%)"

        # Generate stars HTML
        stars_html = "⭐" * int(row['current_hero_stars']) if pd.notna(row['current_hero_stars']) else ""

        html_content += f"""
            <tr>
                <td class="rank">{row['rank']}</td>
                <td class="hero-cell">
                    <img src="{row['hero_pfp_url']}" class="hero-image" alt="{row['hero_handle']}">
                    <span>{row['hero_handle']}</span>
                </td>
                <td style="color: {score_color};">{int(row['hero_fantasy_score'])}</td>
                <td>{format_percentage(row['card_utilization'])}</td>
                <td>{stars_html}</td>
                <td>{int(row['reach']):,}</td>
                <td>{int(row['views']):,}</td>
                <td>{int(row['tweets']):,}</td>
            </tr>
        """

    html_content += """
        </table>
        <script src="./script.js"></script>
    </body>
    </html>
    """
    
    with open("pages/hero_scorecenter.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    print("HTML file generated successfully!")

if __name__ == "__main__":
    # Get the data
    df_heroes, latest_score_timestamp = get_heroes_data()
    
    # Calculate min and max scores
    min_fan_score = df_heroes['hero_fantasy_score'].min()
    max_fan_score = df_heroes['hero_fantasy_score'].max()

    # Generate and save the HTML file
    generate_html(df_heroes, latest_score_timestamp)
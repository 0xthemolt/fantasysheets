import psycopg2
from jinja2 import Template
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import json
from datetime import datetime, timedelta


# Load configuration from config.json
with open('C:/fantasy_top_analysis/pages/config.json', 'r') as config_file:
    config = json.load(config_file)

# PLACEHOLDER_IMAGE = config['placeholder_image']    "placeholder_image": "https://pbs.twimg.com/profile_images/1754590022664101888/geh_HFDq_400x400.jpg",
TOURNAMENT_NUMBER = config['tournament_number']
LEAGUE_IMAGES = config['league_images']
REWARD_IMAGES = config['reward_images']


# Define your query
query = f"""
WITH player_sample AS (
    SELECT tournament_unique_key
    ,COUNT(DISTINCT tournament_player_deck_id) AS total_decks
    ,COUNT(DISTINCT tournament_player_deck_id)*5 AS total_cards
    FROM agg.TournamentOwnership
    WHERE 1=1
    -- player_rank <= 100
    --AND tournament_unique_key = 'Main 10'
    group by tournament_unique_key
)
SELECT 
    a.hero_handle,  --0
    COALESCE(hero_stars,2) hero_stars,  --1
    coalesce(ghwss.hero_pfp_image_url  , 'https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v1/neutral/' || a.hero_handle || '.png')  as hero_pfp_url,  --2
   -- 'https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v1/neutral/' || a.hero_handle || '.png' hero_pfp_url,
    COUNT(*) AS card_usage_count, --3
    ROUND(100*(COUNT(*)::NUMERIC/MAX(total_cards)), 1) AS card_ownership,  --4
    MAX(ROUND(COALESCE(ghst.fantasy_score,0), 0)) AS tournament_fan_score,  --5
    MAX(ROUND(COALESCE(ghst.reach,0), 0)) AS tournament_reach,  --6
    MAX(ROUND(COALESCE(ghst.views,0), 0)) AS tournament_views,  --7
    MAX(ROUND(COALESCE(ghst.tweet_count,0), 0)) AS tournament_tweets, --8
    MIN(a.db_updated_cst) AS ownership_timestamp, --9
    MAX(total_decks) AS total_decks, --10
    MAX(total_cards) as total_cards, --11
    MIN(a.db_updated_cst)::timestamp AS score_timestamp,  --12
    ROUND(100*(COUNT(*)::NUMERIC/MAX(sup.aggregate_cards)),0) AS card_supply_usage  --13
FROM agg.TournamentOwnership a
LEFT JOIN flatten.GET_HEROS_WITH_STATS_TOURNAMENT ghst
    on a.hero_id = ghst.hero_id
    and a.tournament_id = ghst.tournament_id
LEFT JOIN flatten.get_heros_with_stats_snapshot ghwss 
    ON a.hero_id = ghwss.hero_id 
    AND ghwss.snapshot_rank = 1 
left join flatten.get_supply_PER_HERO_ID sup
	on a.hero_id  = sup.hero_id 
	and sup.snapshot_rank  = 1
CROSS JOIN player_sample
WHERE 1=1
and a.hero_handle not IN ('satsdart','delucinator')
and a.tournament_unique_key = player_sample.tournament_unique_key
and a.tournament_unique_key  = 'Main {TOURNAMENT_NUMBER}'
GROUP BY 1, 2, 3
ORDER BY CAST(COUNT(*) AS FLOAT)/100 DESC
"""

try:
    conn = psycopg2.connect("dbname='0xthemolt' user='postgres' host='localhost' password='admin'")
except:
    print("I am unable to connect to the database")
    
# Execute the query and fetch data
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()

# Close cursor and connection
cur.close()
conn.close()

# Function to convert hero_stars to star emojis
def convert_to_stars(hero_stars):
    return '⭐' * hero_stars

# Helper function to format numbers
def format_number(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return str(value)
    
# Convert hero_stars to star emojis in the rows
rows = [(row[0], convert_to_stars(row[1]), row[2], row[3], float(row[4]), float(row[5]), round(float(row[6])), round(float(row[7])), round(float(row[8])), row[9], row[10], row[11], row[12], int(row[13])) for row in rows]

# Organize rows by hero_stars for card ownership
stars_dict_ownership = {}
for row in rows:
    stars = row[1]
    if stars not in stars_dict_ownership:
        stars_dict_ownership[stars] = []
    stars_dict_ownership[stars].append(row)  # Remove the limit of 5

# Sort stars_dict by hero_stars value (ascending)
stars_dict_ownership = dict(sorted(stars_dict_ownership.items(), key=lambda x: len(x[0])))

# Organize rows by hero_stars for fan score
stars_dict_fan_score = {}
for row in sorted(rows, key=lambda x: x[5], reverse=True):  # Sort by fan score descending
    stars = row[1]
    if stars not in stars_dict_fan_score:
        stars_dict_fan_score[stars] = []
    if len(stars_dict_fan_score[stars]) < 40:  # Get only top 10 for each star value
        stars_dict_fan_score[stars].append(row)

# Sort stars_dict by hero_stars value (ascending)
stars_dict_fan_score = dict(sorted(stars_dict_fan_score.items(), key=lambda x: len(x[0])))

# Organize rows by hero_stars for card supply usage
stars_dict_supply_usage = {}
for row in sorted(rows, key=lambda x: x[13], reverse=True):  # Sort by card supply usage descending
    stars = row[1]
    if stars not in stars_dict_supply_usage:
        stars_dict_supply_usage[stars] = []
    stars_dict_supply_usage[stars].append(row)  # Remove the limit of 5

# Sort stars_dict by hero_stars value (ascending)
stars_dict_supply_usage = dict(sorted(stars_dict_supply_usage.items(), key=lambda x: len(x[0])))

# Get the latest score_timestamp and calculate the time difference in minutes
latest_score_timestamp = max(row[12] for row in rows)
latest_score_timestamp_formatted = latest_score_timestamp.strftime("%Y-%m-%d %H:%M")
current_time = datetime.now()  # Get the current local time
time_diff_minutes = int((current_time - latest_score_timestamp).total_seconds() / 60)

print(latest_score_timestamp_formatted)

# Prepare ownership for conditional formatting
all_ownerships = [record[4] for records in stars_dict_ownership.values() for record in records]
min_ownership = min(all_ownerships)
max_ownership = max(all_ownerships)
norm_ownership = plt.Normalize(min_ownership, max_ownership)
cmap_ownership = cm.get_cmap('viridis')  # Use viridis for better contrast with white text

def get_ownership_color(ownership, min_ownership, max_ownership):
    norm = plt.Normalize(min_ownership, max_ownership)
    rgba = cmap_ownership(norm(ownership))
    return f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {rgba[3]})"

# Prepare supply usage for conditional formatting
all_supplyusage = [record[13] for records in stars_dict_ownership.values() for record in records]
min_supplyusage = min(all_supplyusage)
max_supplyusage = max(all_supplyusage)
norm_supplyusage = plt.Normalize(min_supplyusage, max_supplyusage)
cmap_supplyusage = cm.get_cmap('viridis')  # Use viridis for better contrast with white text

def get_supplyusage_color(supplyusage, min_supplyusage, max_supplyusage):
    norm = plt.Normalize(min_supplyusage, max_supplyusage)
    rgba = cmap_supplyusage(norm(supplyusage))
    return f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {rgba[3]})"

# Prepare fan_score for conditional formatting
all_scores = [record[5] for records in stars_dict_fan_score.values() for record in records]
min_score = min(all_scores)
max_score = max(all_scores)
norm_fan_score = plt.Normalize(min_score, max_score)
cmap_fan_score = cm.get_cmap('RdYlGn')

def get_fan_score_color(score, min_score, max_score):
    norm = plt.Normalize(min_score, max_score)
    rgba = cmap_fan_score(norm(score))
    return f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {rgba[3]})"

views_cap = 1000000  # Set the cap value as needed

# Normalize the views, tweets, and reach for conditional formatting
all_views = [record[7] for records in stars_dict_fan_score.values() for record in records]
all_tweets = [record[8] for records in stars_dict_fan_score.values() for record in records]
all_reach = [record[6] for records in stars_dict_fan_score.values() for record in records]

min_views, max_views = min(all_views), max(all_views)
min_tweets, max_tweets = min(all_tweets), max(all_tweets)
min_reach, max_reach = min(all_reach), max(all_reach)

def normalize_value(value, min_value, max_value):
    return (value - min_value) / (max_value - min_value)

norm_views = plt.Normalize(0, 1)
norm_tweets = plt.Normalize(0, 1)
norm_reach = plt.Normalize(0, 1)

cmap_views = cm.get_cmap('RdYlGn')
cmap_tweets = cm.get_cmap('RdYlGn')
cmap_reach = cm.get_cmap('RdYlGn')

def get_color(value, min_value, max_value, cmap, norm_func):
    normalized = normalize_value(value, min_value, max_value)
    rgba = cmap(norm_func(normalized))
    return f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {rgba[3]})"

def get_views_color(views):
    return get_color(views, min_views, max_views, cmap_views, norm_views)

def get_tweets_color(tweets):
    return get_color(tweets, min_tweets, max_tweets, cmap_tweets, norm_tweets)

def get_reach_color(reach):
    return get_color(reach, min_reach, max_reach, cmap_reach, norm_reach)


# Define the HTML template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player Data</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #000; color: #fff; }
        .sections { display: flex; justify-content: space-between; flex-wrap: wrap; }
        .section { width: 12%; margin-bottom: 20px; }
        .section h2 { text-align: center; color: #FFD700; font-size: 0.9em; margin: 5px 0; }  /* Reduced margin-bottom */
        h1 { font-size: 1.5em; }  /* Smaller font size for h1 tag */
        h2 { text-align: center; }  /* Center-align h2 elements */
        .timestamp { font-size: 0.5em; color: #aaa; text-align: center; margin: 5px 0; }  /* Reduced margin-bottom */
        .small-text { font-size: 0.7em; color: #aaa; text-align: center; margin: 5px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.7em; border-radius: 10px; overflow: hidden; }
        th, td { padding: 8px; color: #fff; text-align: center; }
        th { background-color: #141515; border-bottom: 1px solid #fff; text-transform: uppercase; }
        td { background-color: #141515; border-top: 1px solid #ddd; font-size: 1em; }
        td { border-bottom: 1px solid #444; } /* finer grey line */
        .card img { width: 30px; height: 30px; border-radius: 50%; display: block; margin: 0 auto; }
        .card p { font-size: 0.6em; text-align: center; }
        table tr:last-child td { border-bottom: none; } /* No horizontal line at the bottom */
        .black-text { color: #000; }
        .multi-line div { margin: 5px 0; }
        #search-container {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
        #search-box {
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        .highlight td {
            border: none;
        }
        .highlight td:first-child {
            border-left: 3px solid white;
        }
        .highlight td:last-child {
            border-right: 3px solid white;
        }
        .highlight {
            border-top: 3px solid white;
            border-bottom: 3px solid white;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Update the search functionality
            const searchBox = document.getElementById('search-box');
            const cards = document.querySelectorAll('.card');

            searchBox.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                cards.forEach(card => {
                    const heroName = card.querySelector('p').textContent.toLowerCase();
                    const row = card.closest('tr');
                    if (searchTerm && heroName.includes(searchTerm)) {
                        row.classList.add('highlight');
                    } else {
                        row.classList.remove('highlight');
                    }
                });
            });
        });
    </script>
</head>
<body>
<div id="search-container">
    <input type="text" id="search-box" placeholder="Search hero...">
</div>
<h2>Main 22 - All Heroes By Stars & % Utilized of Total Cards</h2>
    <div class="small-text">
        <span>Total Decks: {{ rows[0][10] }} | Total Cards: {{ rows[0][11] }}  |  Last updated: {{ latest_score_timestamp }} UTC </span>
    </div>
    <div class="sections">
        {% for stars, records in stars_dict_ownership.items() %}
        <div class="section">
            <h2>{{ stars }}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hero</th>
                        <th>Utilization %</th>
                        <th>Fan Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                    <tr>
                        <td>
                            <div class="card">
                                <img src="{{ record[2] }}" alt="Hero Picture">
                                <p>{{ record[0] }}</p>
                            </div>
                        </td>
                        <td class="black-text" style="background-color:  {{ get_ownership_color(record[4]) }}">{{ record[4] }}% ({{ record[3] }})</td>
                        <td style="color: {{ get_fan_score_color(record[5]) }}">{{ round(record[5]) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </div>
    
    
    <h2>Main 22 - All Heroes By Stars & % Supply In Decks</h2>
    <div class="sections">
        {% for stars, records in stars_dict_supply_usage.items() %}
        <div class="section">
            <h2>{{ stars }}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hero</th>
                        <th>Supply Usage %</th>
                        <th>Fan Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                    <tr>
                        <td>
                            <div class="card">
                                <img src="{{ record[2] }}" alt="Hero Picture">
                                <p>{{ record[0] }}</p>
                            </div>
                        </td>
                        <td class="black-text" style="background-color: {{ get_supplyusage_color(record[13]) }}">{{ record[13] }}% ({{ record[3] }})</td>
                        <td style="color: {{ get_fan_score_color(record[5]) }}">{{ round(record[5]) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </div>

    <h2>Main 22 - Heros by Stars & Highest Fan Score</h2>
    <div class="sections">
        {% for stars, records in stars_dict_fan_score.items() %}
        <div class="section">
            <h2>{{ stars }}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hero</th>
                        <th>Fan Score</th>
                        <th>Views | Posts | Reach</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                    <tr>
                        <td>
                            <div class="card">
                                <img src="{{ record[2] }}" alt="Hero Picture">
                                <p>{{ record[0] }}</p>
                            </div>
                        </td>
                        <td class="black-text" style="background-color: {{ get_fan_score_color(record[5]) }}">{{ round(record[5]) }}</td>
                        <td class="multi-line">
                            <!--<div style="color: {{ get_views_color(record[7]) }}">👀 - {{ format_number(record[7]) }}</div>-->
                            <!--<div style="color: {{ get_tweets_color(record[8]) }}">🐦 - {{ format_number(record[8]) }}</div>-->
                            <!--<div style="color: {{ get_reach_color(record[6]) }}">🫳 - {{ format_number(record[6]) }}</div>-->
                            <div>👀 - {{ format_number(record[7]) }}</div> 
                            <div>🐦 - {{ format_number(record[8]) }}</div>
                            <div>🫳 - {{ format_number(record[6]) }}</div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# # Render the template with data
# template = Template(html_template)
# html_content = template.render(
#     stars_dict_ownership=stars_dict_ownership, 
#     stars_dict_fan_score=stars_dict_fan_score, 
#     stars_dict_supply_usage=stars_dict_supply_usage,
#     get_ownership_color=get_ownership_color, 
#     get_supplyusage_color=get_supplyusage_color,
#     get_fan_score_color=get_fan_score_color, 
#     get_views_color=get_views_color, 
#     get_tweets_color=get_tweets_color, 
#     get_reach_color=get_reach_color, 
#     round=round, 
#     format_number=format_number,  # Pass format_number function here
#     latest_score_timestamp=latest_score_timestamp_formatted,  # Pass the formatted timestamp
#     time_diff_minutes=time_diff_minutes,
#     rows=rows  # Pass the rows to access total_decks and total_cards
# )

# # Write the HTML content to a file with UTF-8 encoding
# with open("player_data.html", "w", encoding="utf-8") as file:
#     file.write(html_content)

# print("HTML file has been generated.")

def create_html_content(title, data_dict, main_color_func, main_value_index, count_index, fan_score_color_func, additional_columns=None, include_percentage=True):
    # Calculate min and max values for the main data
    all_main_values = [record[main_value_index] for records in data_dict.values() for record in records]
    min_main_value = min(all_main_values)
    max_main_value = max(all_main_values)

    # Calculate min and max values for fan score
    all_fan_scores = [record[5] for records in data_dict.values() for record in records]
    min_fan_score = min(all_fan_scores)
    max_fan_score = max(all_fan_scores)

    # Create specific color functions
    def get_specific_main_color(value):
        return main_color_func(value, min_main_value, max_main_value)

    def get_specific_fan_score_color(value):
        return fan_score_color_func(value, min_fan_score, max_fan_score)
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #000; color: #fff; }
        .sections { display: flex; justify-content: space-between; flex-wrap: wrap; }
        .section { width: 12%; margin-bottom: 20px; }
        .section h2 { text-align: center; color: #FFD700; font-size: 0.9em; margin: 5px 0; }  /* Reduced margin-bottom */
        h1 { font-size: 1.5em; }  /* Smaller font size for h1 tag */
        h2 { text-align: center; }  /* Center-align h2 elements */
        .timestamp { font-size: 0.5em; color: #aaa; text-align: center; margin: 5px 0; }  /* Reduced margin-bottom */
        .small-text { font-size: 0.7em; color: #aaa; text-align: center; margin: 5px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.7em; border-radius: 10px; overflow: hidden; }
        th, td { padding: 8px; color: #fff; text-align: center; }
        th { background-color: #141515; border-bottom: 1px solid #fff; text-transform: uppercase; }
        td { background-color: #141515; border-top: 1px solid #ddd; font-size: 1em; }
        td { border-bottom: 1px solid #444; } /* finer grey line */
        .card img { width: 30px; height: 30px; border-radius: 50%; display: block; margin: 0 auto; }
        .card p { font-size: 0.6em; text-align: center; }
        table tr:last-child td { border-bottom: none; } /* No horizontal line at the bottom */
        .black-text { color: #000; }
        .multi-line div { margin: 5px 0; }
        #search-container {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
        #search-box {
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        .highlight td {
            border: none;
        }
        .highlight td:first-child {
            border-left: 3px solid white;
        }
        .highlight td:last-child {
            border-right: 3px solid white;
        }
        .highlight {
            border-top: 3px solid white;
            border-bottom: 3px solid white;
        }
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const searchBox = document.getElementById('search-box');
                const rows = document.querySelectorAll('table tr');

                searchBox.addEventListener('input', function() {
                    const searchTerm = this.value.toLowerCase();
                    rows.forEach(row => {
                        const heroName = row.querySelector('.card p')?.textContent.toLowerCase();
                        if (heroName) {
                            if (searchTerm && heroName.includes(searchTerm)) {
                                row.classList.add('highlight');
                            } else {
                                row.classList.remove('highlight');
                            }
                        }
                    });
                });
            });
        </script>
    </head>
    <body>
    <div class="title-container">
        <h1>
            <a href="home.html" class="home-link">
                <i class="fas fa-home"></i>
            </a>
            {{ title }}
        </h1>
        <div class="tournament-badge">Main {TOURNAMENT_NUMBER}</div>
    </div>
    <div id="search-container">
        <input type="text" id="player-search-box" class="search-box" placeholder="Search Players">
    </div>
    <div class="small-text">
        <span>Total Decks: {{ rows[0][10] }} | Total Cards: {{ rows[0][11] }}  |  Last updated: {{ latest_score_timestamp }} UTC </span>
    </div>
    <div class="sections">
        {% for stars, records in data_dict.items() %}
        <div class="section">
            <h2>{{ stars }}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hero</th>
                        <th>{{ additional_columns[0] if additional_columns else 'Value' }}</th>
                        {% if additional_columns and additional_columns|length > 1 %}
                            <th>{{ additional_columns[1] }}</th>
                        {% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                    <tr>
                        <td>
                            <div class="card">
                                <img src="{{ record[2] }}" alt="Hero Picture">
                                <p>{{ record[0] }}</p>
                            </div>
                        </td>
                        <td class="black-text" style="background-color: {{ get_specific_main_color(record[main_value_index]) }}">
                            {% if include_percentage %}
                                {{ record[main_value_index] }}% {% if count_index is not none %}({{ record[count_index] }}){% endif %}
                            {% else %}
                                {{ round(record[main_value_index]) }}
                            {% endif %}
                        </td>
                        {% if additional_columns and additional_columns|length > 1 %}
                            <td class="multi-line">
                                <div>👀 - {{ format_number(record[7]) }}</div> 
                                <div>🐦 - {{ format_number(record[8]) }}</div>
                                <div>🫳 - {{ format_number(record[6]) }}</div>
                            </td>
                        {% endif %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </div>
    </body>
    </html>
    """
    template = Template(html_template)
    return template.render(
        title=title,
        data_dict=data_dict,
        get_specific_main_color=get_specific_main_color,
        get_specific_fan_score_color=get_specific_fan_score_color,
        additional_columns=additional_columns,
        round=round,
        format_number=format_number,
        latest_score_timestamp=latest_score_timestamp_formatted,
        rows=rows,
        main_value_index=main_value_index,
        count_index=count_index,
        include_percentage=include_percentage
    )

# Generate HTML for ownership by star
ownership_html = create_html_content(
    "Main 22 - All Heroes By Stars & % Utilized of Total Cards",
    stars_dict_ownership,
    get_ownership_color,
    4,  # main_value_index
    3,  # count_index
    get_fan_score_color,
    ["Utilization %", "Fan Score"],
    include_percentage=True
)

# Generate HTML for supply utilization by star
supply_html = create_html_content(
    "Main 22 - All Heroes By Stars & % Supply In Decks",
    stars_dict_supply_usage,
    get_supplyusage_color,
    13,  # main_value_index
    3,  # count_index
    get_fan_score_color,
    ["Supply Usage %", "Fan Score"],
    include_percentage=True
)

# Generate HTML for scores by star
scores_html = create_html_content(
    "Main 22 - Heroes by Stars & Highest Fan Score",
    stars_dict_fan_score,
    get_fan_score_color,
    5,  # main_value_index
    None,  # count_index
    get_fan_score_color,
    ["Fan Score", "Views | Posts | Reach"],
    include_percentage=False
)

# Write the HTML content to separate files
with open("hero_deck_utilization.html", "w", encoding="utf-8") as file:
    file.write(ownership_html)

with open("hero_supply_utilization.html", "w", encoding="utf-8") as file:
    file.write(supply_html)

with open("hero_analytics.html", "w", encoding="utf-8") as file:
    file.write(scores_html)

print("Three separate HTML files have been generated.")
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
        select town.*
            from agg.TournamentOwnership town
            join flatten.get_heros_with_stats_snapshot ghwss on town.hero_id = ghwss.hero_id and ghwss.snapshot_rank = 1 and is_deleted = 0
            where town.tournament_unique_key   in ('Main {TOURNAMENT_NUMBER}')
        )
        ,all_heroes as (
            select hero_id,COUNT(*) as hero_usage_count,ROUND(MAX(case when hero_rarity = 'common' then hero_fantasy_score else 0 end),0) hero_fantasy_score, MIN(db_updated_cst) db_updated_cst from tournament_base group by 1
        )
        ,unique_decks AS (
            SELECT COUNT(distinct tournament_player_deck_id) unique_decks
            FROM tournament_base
        )
        ,unique_decks_by_league AS (
            SELECT tournament_league_unique_key,COUNT(distinct tournament_player_deck_id) unique_decks
            FROM tournament_base
            group by 1
        )
        , reverse as (
            select hero_id,COUNT(*)::numeric /  MAX(b.unique_decks)  pct_total
            from  tournament_base a
            left join unique_decks_by_league b on a.tournament_league_unique_key = b.tournament_league_unique_key
            where a.tournament_name  in ('Reverse Score')
            group by 1
        )
        , bronze as (
            select hero_id,COUNT(*)::numeric /  MAX(b.unique_decks)  pct_total
            from  tournament_base a
            left join unique_decks_by_league b on a.tournament_league_unique_key = b.tournament_league_unique_key
            where a.tournament_name  in ('Bronze')
            group by 1
        )
        , silver as (
            select hero_id,COUNT(*)::numeric /  MAX(b.unique_decks)  pct_total
            from  tournament_base a
            left join unique_decks_by_league b on a.tournament_league_unique_key = b.tournament_league_unique_key
            where a.tournament_name  in ('Silver')
            group by 1
        )
        , gold as (
            select hero_id,COUNT(*)::numeric /  MAX(b.unique_decks)  pct_total
            from  tournament_base a
            left join unique_decks_by_league b on a.tournament_league_unique_key = b.tournament_league_unique_key
            where a.tournament_name  in ('Gold')
            group by 1
        )
        , elite as (
            select hero_id,COUNT(*)::numeric /  MAX(b.unique_decks)  pct_total
            from  tournament_base a
            left join unique_decks_by_league b on a.tournament_league_unique_key = b.tournament_league_unique_key
            where a.tournament_name  in ('Elite')
            group by 1
        )
        select ghwss.hero_handle,
            ah.hero_fantasy_score,
            ah.hero_usage_count,
            ud.unique_decks,
            ah.hero_usage_count::numeric / ud.unique_decks  as total_utilization,
            e.pct_total elite_utilization,
            g.pct_total gold_utilization,
            s.pct_total silver_utilization,
            b.pct_total bronze_utilization,
            r.pct_total as reverse_utilization,
            coalesce(ghwss.hero_pfp_image_url, 'https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v1/neutral/' || ghwss.hero_handle || '.png') as hero_pfp_url,
            ah.db_updated_cst::timestamp AS score_timestamp
        from all_heroes ah
        JOIN flatten.get_heros_with_stats_snapshot ghwss 
            ON ah.hero_id = ghwss.hero_id 
            AND ghwss.snapshot_rank = 1 
        cross join unique_decks ud
        left join reverse r on ah.hero_id = r.hero_id
        left join bronze b on ah.hero_id = b.hero_id
        left join silver s on ah.hero_id = s.hero_id
        left join gold g on ah.hero_id = g.hero_id
        left join elite e on ah.hero_id = e.hero_id
        order by 5 desc
    """
    df_heroes = pd.read_sql(query, conn)
    
    # Close the connection
    conn.close()
    
    # After fetching the heroes data, sort by hero_fantasy_score in descending order
    df_heroes = df_heroes.sort_values(by='hero_fantasy_score', ascending=False)

    # Add a rank column based on total_utilization, skipping identical values
    df_heroes['rank'] = df_heroes['total_utilization'].rank(method='dense', ascending=False).astype(int)

    # Calculate the latest timestamp and time difference
    latest_score_timestamp = max(df_heroes['score_timestamp'])
    latest_score_timestamp = df_heroes['score_timestamp'].max().strftime("%Y-%m-%d %H:%M")
    # Calculate total decks and total cards
    total_heroes = len(df_heroes)
    total_decks = df_heroes['unique_decks'].iloc[0]
    total_cards = total_decks * 5

    return df_heroes, latest_score_timestamp, total_heroes, total_decks, total_cards


# Function to get color based on value
def get_color(value, vmin, vmax):
    # Convert Decimal to float if necessary
    value = float(value) if isinstance(value, Decimal) else value
    vmin = float(vmin) if isinstance(vmin, Decimal) else vmin
    vmax = float(vmax) if isinstance(vmax, Decimal) else vmax

    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap('viridis')
    rgb = cmap(norm(value))[:3]  # Get RGB values
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

# Function to format utilization as percentage with color
def format_utilization(value, vmin, vmax):
    if pd.isna(value) or value is None:
        return '-'
    color = get_color(value, vmin, vmax)
    return f'<span style="color: {color}">{float(value):.1%}</span>'

# Function to format utilization as percentage with color and additional text
def format_utilization_with_count(value, vmin, vmax, hero_usage_count, unique_decks):
    if pd.isna(value) or value is None:
        return '-'
    color = get_color(value, vmin, vmax)
    return f'<span style="color: {color}">{float(value):.1%}</span><br><span class="small-count">({hero_usage_count} of {unique_decks})</span>'

def get_fan_score_color(score, min_score, max_score):
    norm = Normalize(min_score, max_score)
    rgba = plt.get_cmap('RdYlGn')(norm(score))  # Use RdYlGn colormap instead of viridis
    return f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {rgba[3]})"

def generate_html(df_heroes, latest_score_timestamp, total_heroes, total_decks, total_cards):

        # Calculate min and max values for each utilization column
    utilization_columns = {
        'elite_utilization': df_heroes['elite_utilization'].dropna(),
        'gold_utilization': df_heroes['gold_utilization'].dropna(),
        'silver_utilization': df_heroes['silver_utilization'].dropna(),
        'bronze_utilization': df_heroes['bronze_utilization'].dropna(),
        'reverse_utilization': df_heroes['reverse_utilization'].dropna(),
        'total_utilization': df_heroes['total_utilization'].dropna()
    }
    
    league_min_max = {
        column: (values.min(), values.max()) 
        for column, values in utilization_columns.items()
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hero Utilization by League</title>
        <link rel="stylesheet" href="./styles.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    </head>
    <body>
        <div class="title-container">
            <h1>
                <a href="home.html" class="home-link">
                    <i class="fas fa-home"></i>
                </a>
                Hero Utilization by League
            </h1>
            <div class="tournament-badge">Main {TOURNAMENT_NUMBER}</div>
        </div>
        <div id="search-container">
            <input type="text" id="hero-search-box" class="search-box" placeholder="Search Heroes">
        </div>
        <div class="small-text">
            <span>Total Heroes: {total_heroes} | Total Decks: {total_decks} | Total Cards: {total_cards} | Last updated: {latest_score_timestamp} UTC</span>
        </div>
        <!-- Main Hero Table -->
        <table id="heroesTable">
            <tr>
                <th>Rank</th>
                <th style="text-align: left;">Hero</th>
                <th class="rank-columns" data-sort="hero_fantasy_score">Score <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down active"></span></div></th>
                <th class="rank-columns" data-sort="elite_utilization"><img src="{LEAGUE_IMAGES['elite']}" class="league-icon" alt="Elite"> Elite <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
                <th class="rank-columns" data-sort="gold_utilization"><img src="{LEAGUE_IMAGES['gold']}" class="league-icon" alt="Gold"> Gold <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
                <th class="rank-columns" data-sort="silver_utilization"><img src="{LEAGUE_IMAGES['silver']}" class="league-icon" alt="Silver"> Silver <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
                <th class="rank-columns" data-sort="bronze_utilization"><img src="{LEAGUE_IMAGES['bronze']}" class="league-icon" alt="Bronze"> Bronze <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
                <th class="rank-columns" data-sort="reverse_utilization">Reverse <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
                <th class="rank-columns" data-sort="total_utilization">Total Utilization <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
            </tr>
    """

    for _, row in df_heroes.iterrows():
        fan_score_color = get_fan_score_color(row['hero_fantasy_score'], min_fan_score, max_fan_score)  # Calculate color
        html_content += f"""
            <tr>
                <td class="rank">{row['rank']}</td>
                <td class="hero-cell">
                    <img src="{row['hero_pfp_url']}" class="hero-image" alt="{row['hero_handle']}">
                    <span>{row['hero_handle']}</span>
                </td>
                <td data-value="{row['hero_fantasy_score'] or 0}" style="color: {fan_score_color};">{int(row['hero_fantasy_score'])}</td> 
                <td data-value="{row['elite_utilization'] or 0}">{format_utilization(row['elite_utilization'], *league_min_max['elite_utilization'])}</td>
                <td data-value="{row['gold_utilization'] or 0}">{format_utilization(row['gold_utilization'], *league_min_max['gold_utilization'])}</td>
                <td data-value="{row['silver_utilization'] or 0}">{format_utilization(row['silver_utilization'], *league_min_max['silver_utilization'])}</td>
                <td data-value="{row['bronze_utilization'] or 0}">{format_utilization(row['bronze_utilization'], *league_min_max['bronze_utilization'])}</td>
                <td data-value="{row['reverse_utilization'] or 0}">{format_utilization(row['reverse_utilization'], *league_min_max['reverse_utilization'])}</td>
                <td data-value="{row['total_utilization'] or 0}">{format_utilization_with_count(row['total_utilization'], *league_min_max['total_utilization'], row['hero_usage_count'], row['unique_decks'])}</td>
            </tr>
        """

    html_content += """
            </tbody>
            </table>
            <script>
            // Function to search
            function searchHeroes() {
                document.getElementById('hero-search-box').addEventListener('input', function() {
                    var searchTerm = this.value.toLowerCase();
                    var rows = document.querySelectorAll('#heroesTable tr');
                    rows.forEach(function(row, index) {
                        if (index === 0) return; // Skip the header row
                        var playerHandleCell = row.querySelector('td:nth-child(2)');
                        if (playerHandleCell) {
                            var playerHandle = playerHandleCell.textContent.toLowerCase();
                            if (playerHandle.includes(searchTerm)) {
                                row.style.display = '';
                            } else {
                                row.style.display = 'none';
                            }
                        }
                    });
                });
            }

             function sortTable(column, descending) {
                var table = document.getElementById("heroesTable");
                var rows = Array.from(table.rows).slice(1); // Convert to array and skip header
                
                // Find the column index based on the data-sort attribute
                var headerCells = table.rows[0].cells;
                var columnIndex = Array.from(headerCells).findIndex(cell => cell.getAttribute('data-sort') === column);
                
                if (columnIndex === -1) return; // Exit if column not found

                // Set ascending to false for hero_fantasy_score to sort in descending order
                const ascending = (column === 'hero_fantasy_score') ? false : !descending; // Always sort hero_fantasy_score in descending order

                rows.sort((a, b) => {
                    let aCell = a.cells[columnIndex];
                    let bCell = b.cells[columnIndex];
                    
                    // Use the raw values stored in data-value
                    let aValue = parseFloat(aCell.getAttribute('data-value')) || 0;
                    let bValue = parseFloat(bCell.getAttribute('data-value')) || 0;

                    return ascending ? aValue - bValue : bValue - aValue; // Adjusted for descending order
                });

                // Reinsert rows in new order
                rows.forEach(row => table.appendChild(row));
                
                updateRanks(); // Call to update ranks after sorting
            }

            // Ensure that the ranking is based on hero_fantasy_score
            function updateRanks() {
                var rows = document.querySelectorAll('#heroesTable tr');
                let currentRank = 1; // Start ranking from 1
                let lastValue = null; // To track the last value for skipping identical ranks
                let lastRank = 1; // To track the last assigned rank

                rows.forEach((row, index) => {
                    if (index === 0) return; // Skip header row
                    var rankCell = row.querySelector('td.rank');
                    if (rankCell) {
                        let currentValue = parseFloat(row.querySelector('td[data-value]').getAttribute('data-value')) || 0;

                        // If the current value is the same as the last value, keep the same rank
                        if (currentValue === lastValue) {
                            rankCell.textContent = lastRank; // Same rank for identical values
                        } else {
                            rankCell.textContent = currentRank; // Assign new rank
                            lastRank = currentRank; // Update lastRank to current
                        }
                        lastValue = currentValue; // Update lastValue to current
                        currentRank++; // Increment rank for next unique value
                    }
                });
            }

            // Add click event listeners to the headers
            document.addEventListener('DOMContentLoaded', function() {
                const headers = document.querySelectorAll('th[data-sort]');
                headers.forEach(header => {
                    header.addEventListener('click', function() {
                        const column = this.getAttribute('data-sort');
                        
                        // Find current sort direction
                        const currentArrow = this.querySelector('.sort-arrow.active');
                        const isAscending = currentArrow && currentArrow.classList.contains('up');
                        
                        // Reset all arrows in all headers
                        document.querySelectorAll('.sort-arrow').forEach(arrow => {
                            arrow.classList.remove('active');
                        });
                        
                        // Update active arrow in clicked header
                        const newArrow = this.querySelector(isAscending ? '.sort-arrow.down' : '.sort-arrow.up');
                        if (newArrow) {
                            newArrow.classList.add('active');
                        }
                        
                        sortTable(column, !isAscending);
                    });
                });
            });

            // Initialize search functionality
            searchHeroes();
            </script>
        </body>
        </html>
        """

    with open("pages/hero_league_utilization.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    print("HTML file generated successfully!")

if __name__ == "__main__":
    # Update the unpacking of return values
    df_heroes, latest_score_timestamp, total_heroes, total_decks, total_cards = get_heroes_data()
    
    # Calculate min and max fan scores based on your data
    min_fan_score = df_heroes['hero_fantasy_score'].min()  # Calculate minimum score
    max_fan_score = df_heroes['hero_fantasy_score'].max()  # Calculate maximum score

    generate_html(df_heroes, latest_score_timestamp, total_heroes, total_decks, total_cards)
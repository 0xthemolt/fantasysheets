import psycopg2
import pandas as pd
import json
import os

# Load configuration from config.json
with open('C:/fantasy_top_analysis/pages/config.json', 'r') as config_file:
    config = json.load(config_file)

# PLACEHOLDER_IMAGE = config['placeholder_image']    "placeholder_image": "https://pbs.twimg.com/profile_images/1754590022664101888/geh_HFDq_400x400.jpg",
TOURNAMENT_NUMBER = config['tournament_number']
LEAGUE_IMAGES = config['league_images']
REWARD_IMAGES = config['reward_images']

def get_players_data():
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
        with base as (
        select gtpp2.tournament_id,gtpp2.player_pic,gtpp2.player_id,gtpp2.player_handle,gtpp2.player_rank,gt2.tournament_name,gtpp2.db_updated_cst::timestamp as timestamp
        from flatten.get_tournament_past_players gtpp2 
        join flatten.get_tournaments gt2 
            on gtpp2.tournament_id = gt2.tournament_id
        where gtpp2.tournament_unique_key = 'Main {TOURNAMENT_NUMBER}'
        )
        ,best_elite as (
        select player_id,player_rank,row_number() over (partition by player_id order by player_rank asc) rank_seq
        from base 
        where tournament_name = 'Elite'
        )
        ,best_gold as (
        select player_id,player_rank,row_number() over (partition by player_id order by player_rank asc) rank_seq
        from base 
        where tournament_name = 'Gold'
        )
        ,best_silver as (
        select player_id,player_rank,row_number() over (partition by player_id order by player_rank asc) rank_seq
        from base 
        where tournament_name = 'Silver'
        )
        ,best_bronze as (
        select player_id,player_rank,row_number() over (partition by player_id order by player_rank asc) rank_seq
        from base 
        where tournament_name = 'Bronze'
        )
        ,best_sub as (
        select player_id,player_rank,row_number() over (partition by player_id order by player_rank asc) rank_seq,replace(tournament_name,'Score','') as tournament_name
        from base 
        where tournament_name = 'Reverse Score'
        )
  SELECT 
 		--gt.league,
        gtpp.player_pic,
        gtpp.player_handle,
        elite.player_rank elite_rank,
        gold.player_rank gold_rank,
        silver.player_rank silver_rank,
        bronze.player_rank bronze_rank,
        sub.player_rank sub_rank,
        sub.tournament_name as sub_name,
        min(gtpp.player_rank) as best_rank,
        max(gtpp.player_rank) as worst_rank,
        ROUND(coalesce(sum(reward_eth.reward), 0),2) as reward_eth,
        ROUND(coalesce(sum(reward_pack.reward), 0),0) as reward_pack,
        ROUND(coalesce(sum(reward_fan.reward), 0),0) as reward_fan,
        count(*) as decks,
        MAX(gtpp.timestamp + interval '5 hour') as  timestamp,
        SUM(case when reward_pack.range_end is not null then 1 else 0 END) as itm_decks
    FROM base gtpp 
    LEFT JOIN flatten.get_tournaments gt ON gtpp.tournament_id = gt.tournament_id 
    left join best_elite elite on gtpp.player_id = elite.player_id and elite.rank_seq = 1
	left join best_gold gold on gtpp.player_id = gold.player_id and gold.rank_seq = 1
	left join best_silver silver on gtpp.player_id = silver.player_id and silver.rank_seq = 1
	left join best_bronze bronze on gtpp.player_id = bronze.player_id and bronze.rank_seq = 1
    left join best_sub sub on gtpp.player_id = sub.player_id and sub.rank_seq = 1
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_eth
        ON gtpp.tournament_id = reward_eth.tournament_id 
        AND gtpp.player_rank BETWEEN reward_eth.range_start AND reward_eth.range_end
        AND reward_eth.reward_type = 'ETH'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_pack
        ON gtpp.tournament_id = reward_pack.tournament_id 
        AND gtpp.player_rank BETWEEN reward_pack.range_start AND reward_pack.range_end
        AND reward_pack.reward_type = 'PACK'
    LEFT JOIN flatten.GET_TOURNAMENT_BY_ID reward_fan
        ON gtpp.tournament_id = reward_fan.tournament_id 
        AND gtpp.player_rank BETWEEN reward_fan.range_start AND reward_fan.range_end
        AND reward_fan.reward_type = 'FAN'
   --where gtpp.player_handle = '0xthemolt'
    GROUP BY  gtpp.player_pic,
        gtpp.player_handle,
        elite.player_rank ,
        gold.player_rank ,
        silver.player_rank ,
        bronze.player_rank ,
        sub.player_rank ,
        sub.tournament_name
    having ROUND(coalesce(sum(reward_pack.reward), 0),0) > 0
    ORDER BY reward_eth desc
    """
    df_players = pd.read_sql(query, conn)
    
    # Close the connection
    conn.close()
    
    # Add a rank column based on reward_eth in descending order
    df_players['rank'] = df_players['reward_eth'].rank(method='min', ascending=False).astype(int)
    # Calculate the latest timestamp and time difference
    latest_score_timestamp = max(df_players['timestamp'])
    latest_score_timestamp = df_players['timestamp'].max().strftime("%Y-%m-%d %H:%M")

    return df_players, latest_score_timestamp


def format_reward_fan(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.0f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.0f}k"
    else:
        return str(value)


def generate_html(df_players,latest_score_timestamp):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Player Total Rewards Leaders</title>
        <link rel="stylesheet" href="./styles.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    </head>
    <body>
        <div class="title-container">
            <h1>
                <a href="home.html" class="home-link">
                    <i class="fas fa-home"></i>
                </a>
                Player Total Rewards Leaders
            </h1>
            <div class="tournament-badge">Main {TOURNAMENT_NUMBER}</div>
        </div>
        <div id="search-container">
            <input type="text" id="player-search-box" class="search-box" placeholder="Search Players">
        </div>
        <div class="small-text">
            <span>Last updated: {latest_score_timestamp} UTC</span>
        </div>
        <!-- Main Player Table -->
        <table id="playersTable">
            <tr>
                <th class="player-columns">Rank</th>
                <th style="text-align: left;">Player</th>
                <th class="rank-columns"><img src="{LEAGUE_IMAGES['elite']}" class="league-icon" alt="Elite"> Elite</th>
                <th class="rank-columns"><img src="{LEAGUE_IMAGES['gold']}" class="league-icon" alt="Gold"> Gold</th>
                <th class="rank-columns"><img src="{LEAGUE_IMAGES['silver']}" class="league-icon" alt="Silver"> Silver</th>
                <th class="rank-columns"><img src="{LEAGUE_IMAGES['bronze']}" class="league-icon" alt="Bronze"> Bronze</th>
                <th class="rank-columns reverse-column"><alt="Reverse Score"> Reverse </th>
                <th class="rank-columns itm-decks-column">ITM Decks</th>
                <th class="reward-columns" data-sort="reward_eth">ETH <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down active"></span></div></th>
                <th class="reward-columns" data-sort="reward_pack">Cards <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
                <th class="reward-columns" data-sort="reward_fan">Fan <div class="sort-arrows"><span class="sort-arrow up"></span><span class="sort-arrow down"></span></div></th>
            </tr>
    """

    for _, row in df_players.iterrows():
        html_content += f"""
            <tr>
                <td class="rank">{row['rank']}</td>
                <td class="player-handle">
                    <img src="{row['player_pic']}" class="player-image" alt="{row['player_handle']}"
                        onerror="this.onerror=null; this.src='ft_logo.jpg';">
                    <span>{row['player_handle']}</span>
                </td>
                <td class="rank-columns">{int(row['elite_rank']) if pd.notna(row['elite_rank']) else '-'}</td>
                <td class="rank-columns">{int(row['gold_rank']) if pd.notna(row['gold_rank']) else '-'}</td>
                <td class="rank-columns">{int(row['silver_rank']) if pd.notna(row['silver_rank']) else '-'}</td>
                <td class="rank-columns">{int(row['bronze_rank']) if pd.notna(row['bronze_rank']) else '-'}</td>
                <td class="rank-columns">{int(row['sub_rank']) if pd.notna(row['sub_rank']) else '-'}</td>
                <td class="rank-columns">{int(row['itm_decks'])} / {int(row['decks'])} ({(row['itm_decks'] / row['decks'] * 100):.0f}%)</td>
                <td class="reward-columns" data-value="{row['reward_eth']}">{row['reward_eth']:.2f}<img src="{REWARD_IMAGES['eth']}" class="icon"></td>
                <td class="reward-columns" data-value="{row['reward_pack']}">{int(row['reward_pack'])}<img src="{REWARD_IMAGES['pack']}" class="icon"></td>
                <td class="reward-columns" data-value="{row['reward_fan']}">{format_reward_fan(row['reward_fan'])}<img src="{REWARD_IMAGES['fan']}" class="icon"></td>
            </tr>
        """

    html_content += """
            </tbody>
            </table>
            <script>
            // Function to search players
            function searchPlayers() {
                document.getElementById('player-search-box').addEventListener('input', function() {
                    var searchTerm = this.value.toLowerCase();
                    var rows = document.querySelectorAll('#playersTable tr');
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

            function sortTable(column, ascending) {
                var table = document.getElementById("playersTable");
                var rows = Array.from(table.rows).slice(1); // Convert to array and skip header
                
                // Find the column index based on the data-sort attribute
                var headerCells = table.rows[0].cells;
                var columnIndex = Array.from(headerCells).findIndex(cell => cell.getAttribute('data-sort') === column);
                
                if (columnIndex === -1) return; // Exit if column not found

                rows.sort((a, b) => {
                    let aCell = a.cells[columnIndex];
                    let bCell = b.cells[columnIndex];
                    
                    // Use the raw values stored in data-value
                    let aValue = parseFloat(aCell.getAttribute('data-value')) || 0;
                    let bValue = parseFloat(bCell.getAttribute('data-value')) || 0;

                    return ascending ? aValue - bValue : bValue - aValue;
                });

                // Reinsert rows in new order
                rows.forEach(row => table.appendChild(row));
                
                updateRanks();
            }

            function updateRanks() {
                var rows = document.querySelectorAll('#playersTable tr');
                rows.forEach((row, index) => {
                    if (index === 0) return; // Skip header row
                    var rankCell = row.querySelector('td.rank');
                    if (rankCell) {
                        rankCell.textContent = index;
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
            searchPlayers();
            </script>
        </body>
        </html>
        """

    with open("pages/player_rankings.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    print("HTML file generated successfully!")

if __name__ == "__main__":
    df_players, latest_score_timestamp = get_players_data()  # Capture both return values
    generate_html(df_players, latest_score_timestamp)
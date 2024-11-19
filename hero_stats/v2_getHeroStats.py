import psycopg2
import pandas as pd
import json
from decimal import Decimal

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname="0xthemolt",
            user="postgres",
            password="admin",
            host="localhost",
            port="5432"
        )
    except psycopg2.Error as e:
        raise Exception(f"Unable to connect to database: {e}")

def get_reward_history():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        select gt.tournament_unique_key ,gt.league ,ghwst.hero_handle ,ghwss.hero_name ,
               ghwst.hero_pfp_url ,ghwst.tweet_count as post_count,
               ghwst."views" as views ,ghwst.reach as reach ,ghwst.db_updated_cst as freshness_ts
        from flatten.get_heros_with_stats_tournament ghwst 
        join flatten.get_tournaments gt 
            on ghwst.tournament_id = gt.tournament_id 
        join flatten.get_heros_with_stats_snapshot ghwss 
            on ghwst.hero_id = ghwss.hero_id 
            and ghwss.snapshot_rank = 1
        where gt.league = 'Elite'
        and gt.tournament_seq_nbr <= 17
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Convert results to list of dictionaries
        columns = ['tournament_unique_key', 'league', 'hero_handle', 'hero_name', 'hero_pfp_url', 'post_count', 'views', 'reach', 'freshness_ts']
        hero_data = []
        max_freshness_ts = None
        
        for row in results:
            # Convert Decimal to int/float as needed
            processed_row = []
            for value in row[:-1]:  # Exclude freshness_ts from the hero data
                if isinstance(value, Decimal):
                    processed_row.append(float(value))
                else:
                    processed_row.append(value)
            hero_data.append(dict(zip(columns[:-1], processed_row)))
            
            # Track max freshness_ts
            current_ts = row[-1]  # Get freshness_ts
            if max_freshness_ts is None or current_ts > max_freshness_ts:
                max_freshness_ts = current_ts

        # Create the final structure with metadata
        final_data = {
            "metadata": {
                "freshness_ts": max_freshness_ts.isoformat() if max_freshness_ts else None
            },
            "hero_stats": hero_data
        }

        # Save to JSON file
        output_file = 'pages/hero_stats/hero_stats.json'
        try:
            with open(output_file, 'w') as f:
                json.dump(final_data, f, indent=4)
        except IOError as e:
            raise Exception(f"Error writing to JSON file {output_file}: {e}")
            
        return final_data  # Return the complete structure
        
    except psycopg2.Error as e:
        raise Exception(f"Database error occurred: {e}")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Add this line to execute the function
if __name__ == "__main__":
    get_reward_history()
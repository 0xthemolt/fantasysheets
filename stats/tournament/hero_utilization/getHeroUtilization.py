import psycopg2
import pandas as pd
import json
def get_db_connection():
    return psycopg2.connect(
        dbname="0xthemolt",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

def get_tournament_info():
    conn = get_db_connection()

    # Query the database
    query = f"""select tournament_unique_key,max(tournament_status),min(tournament_seq_nbr) tournament_seq_nbr
        from flatten.get_tournaments gt 
        group by tournament_unique_key 
        order by 3 asc
                limit 2
        """

    # Execute query and store results in DataFrame
    df_tournament = pd.read_sql_query(query, conn)
    
    # Close connection
    conn.close()
    
    return df_tournament

def get_hero_utilization_data(tournament_unique_key):
    conn = get_db_connection()

    # Query the database
    query = f"""
        with tournament_base as (
        select town.hero_id,town.hero_rarity,town.tournament_league_unique_key,town.tournament_player_deck_id,town.tournament_name
        	,ghwst.fantasy_score,ghwst.db_updated_cst
            from agg.TournamentOwnership town
            left join flatten.get_heros_with_stats_tournament ghwst 
            on town.hero_id = ghwst.hero_id 
            and ghwst.tournament_league_unique_key = 'Elite {tournament_unique_key}' /*get scores from elite here*/
            join flatten.get_heros_with_stats_snapshot ghwss on town.hero_id = ghwss.hero_id and ghwss.snapshot_rank = 1 and is_deleted = 0
            where town.tournament_unique_key = '{tournament_unique_key}' 
        )
        ,all_heroes as (
            select hero_id,COUNT(*) as hero_usage_count,MAX(case when hero_rarity = 'common' then fantasy_score else 0 end) hero_fantasy_score, MIN(db_updated_cst) db_updated_cst from tournament_base group by 1
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
            where a.tournament_name  in ('Reverse')
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
            hero_usage_count::NUMERIC/sup.aggregate_cards AS card_supply_utilization, 
            sup.aggregate_cards as card_supply,
            coalesce(ghwss.hero_pfp_image_url, 'https://fantasy-top-cards.s3.eu-north-1.amazonaws.com/v1/neutral/' || ghwss.hero_handle || '.png') as hero_pfp_url,
            ah.db_updated_cst::timestamp + interval '6 hour' AS score_timestamp
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
        left join flatten.get_supply_PER_HERO_ID sup
			on ah.hero_id  = sup.hero_id 
			and sup.snapshot_rank  = 1
        order by 5 desc
    """

        # Execute query and store results in DataFrame
    df_hero_utilization = pd.read_sql_query(query, conn)
    
    # Close connection
    conn.close()
    
    return df_hero_utilization

tournament_df = get_tournament_info()
for _, tournament in tournament_df.iterrows():
    utilization_data = get_hero_utilization_data(tournament['tournament_unique_key'])
    
    # Format filename: lowercase and replace spaces with underscores
    filename = f"{tournament['tournament_unique_key'].lower().replace(' ', '_')}_hero_utilization.json"
    
    # Convert DataFrame to JSON and save to file
    utilization_data.to_json(filename, orient='records')
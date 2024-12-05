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

# Create cursor and execute queries
cursor = conn.cursor()
star_ranges_query = f"""CALL master.update_star_ranges();
select * from master.star_ranges
"""
cursor.execute(star_ranges_query)
star_ranges_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

hero_stats_query = f"""
with l3_main as (
select ghwst.hero_id , PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY ghwst.fantasy_score_afk) l3_main_median  
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
select ghwst.hero_id , ghwst.fantasy_score_afk last_main  
from flatten.get_heros_with_stats_tournament ghwst 
join flatten.get_tournaments gt 
	on ghwst.tournament_id  = gt.tournament_id 
where 1=1
--ghwst.hero_handle  = '0xgaut'
and gt.tournament_seq_nbr  <= 1 
--and gt.tournament_status = 'finished'
and gt.league  = 'Elite'
)
select ghss.hero_handle,ghss.hero_id,ghss.hero_pfp_image_url as hero_image_url
,ghss.seven_day_fantasy_score  as seven_day_score
,gcfs.hero_stars as current_stars
,projected_star.stars as projected_stars
,gcfs.hero_stars - projected_star.stars as projected_stars_diff
,current_star.top_range
,ghss.seven_day_fantasy_score
,l3_main.l3_main_median
,last_main.last_main
from flatten.GET_HEROS_WITH_STATS_SNAPSHOT ghss
left join flatten.get_cards_flags_stars gcfs 
	on ghss.hero_id = gcfs.hero_id 
	and gcfs.snapshot_rank = 1
left join master.star_ranges current_star
	on gcfs.hero_stars = current_star.stars 
left join master.star_ranges projected_star
	on ghss.seven_day_fantasy_score  between projected_star.bottom_range and projected_star.top_range
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

# Create JSON structure and save to file
output_data = {
    "metadata": json.loads(star_ranges_df.to_json(orient='records', date_format='iso')),
    "heroes": json.loads(hero_stats_df.to_json(orient='records', date_format='iso'))
}

# Save to JSON file
output_path = 'pages/hero_stats.json'
print(f"Saving data to: {os.path.abspath(output_path)}")
with open(output_path, 'w') as f:
    json.dump(output_data, f, indent=2)

# Close database connections
cursor.close()
conn.close()

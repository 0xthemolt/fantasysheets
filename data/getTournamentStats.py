import psycopg2
import json
import os
from datetime import datetime
import pandas as pd

def supabase_db_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres.hhcuqhvmzwmehdsaamhn",
        password="Wafj2DCrI6Yjbe4I",
        host="aws-0-us-west-1.pooler.supabase.com",
        port="5432"
    )

# postgresql://postgres.hhcuqhvmzwmehdsaamhn:$&roct8&rgp4NE@aws-0-us-west-1.pooler.supabase.com:5432/postgres

# First query into league_decks_df
conn = supabase_db_connection()
cursor = conn.cursor()
league_decks_query = f"""
with override as (
 SELECT 'Main 50'  AS tournament_unique_key, 'Diamond' as league,1507 as registered_decks,652 AS player_count union all
  SELECT 'Main 50'  AS tournament_unique_key, 'Gold' as league,3133 as registered_decks,946 AS player_count union all
   SELECT 'Main 50'  AS tournament_unique_key, 'Silver' as league,5261 as registered_decks,1850 AS player_count union all
    SELECT 'Main 50'  AS tournament_unique_key, 'Bronze' as league,9217 as registered_decks,2877 AS player_count union all
     SELECT 'Main 50'  AS tournament_unique_key, 'Reverse' as league,5644 as registered_decks,1514 AS player_count union all
      SELECT 'Main 51'  AS tournament_unique_key, 'Diamond' as league,1674 as registered_decks,676 AS player_count union all
  SELECT 'Main 51'  AS tournament_unique_key, 'Gold' as league,3321 as registered_decks,945 AS player_count union all
   SELECT 'Main 51'  AS tournament_unique_key, 'Silver' as league,5164 as registered_decks,1789 AS player_count union all
    SELECT 'Main 51'  AS tournament_unique_key, 'Bronze' as league,9449 as registered_decks,2840 AS player_count union all
     SELECT 'Main 51'  AS tournament_unique_key, 'Reverse' as league,5449 as registered_decks,1526 AS player_count union all
      SELECT 'Main 52'  AS tournament_unique_key, 'Diamond' as league,1593 as registered_decks,600 AS player_count union all
  SELECT 'Main 52'  AS tournament_unique_key, 'Gold' as league,2913 as registered_decks,878 AS player_count union all
   SELECT 'Main 52'  AS tournament_unique_key, 'Silver' as league,5192 as registered_decks,1639 AS player_count union all
    SELECT 'Main 52'  AS tournament_unique_key, 'Bronze' as league,10820 as registered_decks,2886 AS player_count union all
     SELECT 'Main 52'  AS tournament_unique_key, 'Reverse' as league,5126 as registered_decks,1349 AS player_count union all
SELECT 'Main 53'  AS tournament_unique_key, 'Diamond' as league,1576 as registered_decks,578 AS player_count union all
  SELECT 'Main 53'  AS tournament_unique_key, 'Gold' as league,2648 as registered_decks,839 AS player_count union all
   SELECT 'Main 53'  AS tournament_unique_key, 'Silver' as league,5006 as registered_decks,1610 AS player_count union all
    SELECT 'Main 53'  AS tournament_unique_key, 'Bronze' as league,12127 as registered_decks,3032 AS player_count union all
     SELECT 'Main 53'  AS tournament_unique_key, 'Reverse' as league,3470 as registered_decks,946 AS player_count union all
     SELECT 'Main 54'  AS tournament_unique_key, 'Diamond' as league,1371 as registered_decks,553 AS player_count union all
  SELECT 'Main 54'  AS tournament_unique_key, 'Gold' as league,2942 as registered_decks,830 AS player_count union all
   SELECT 'Main 54'  AS tournament_unique_key, 'Silver' as league,5492 as registered_decks,1608 AS player_count union all
    SELECT 'Main 54'  AS tournament_unique_key, 'Bronze' as league,12652 as registered_decks,3071 AS player_count union all
     SELECT 'Main 54'  AS tournament_unique_key, 'Reverse' as league,3663 as registered_decks,1007 AS player_count union all 
          SELECT 'Main 55'  AS tournament_unique_key, 'Diamond' as league,1777 as registered_decks,583 AS player_count union all
  SELECT 'Main 55'  AS tournament_unique_key, 'Gold' as league,2867 as registered_decks,821 AS player_count union all
   SELECT 'Main 55'  AS tournament_unique_key, 'Silver' as league,4872 as registered_decks,1475 AS player_count union all
    SELECT 'Main 55'  AS tournament_unique_key, 'Bronze' as league,11075 as registered_decks,2899 AS player_count union all
     SELECT 'Main 55'  AS tournament_unique_key, 'Reverse' as league,4088 as registered_decks,1045 AS player_count union all
               SELECT 'Main 56'  AS tournament_unique_key, 'Diamond' as league,1642 as registered_decks,569 AS player_count union all
  SELECT 'Main 56'  AS tournament_unique_key, 'Gold' as league,2720 as registered_decks,788 AS player_count union all
   SELECT 'Main 56'  AS tournament_unique_key, 'Silver' as league,5019 as registered_decks,1471 AS player_count union all
    SELECT 'Main 56'  AS tournament_unique_key, 'Bronze' as league,12148 as registered_decks,2906 AS player_count union all
     SELECT 'Main 56'  AS tournament_unique_key, 'Reverse' as league,3691 as registered_decks,861 AS player_count union all
                    SELECT 'Main 57'  AS tournament_unique_key, 'Diamond' as league,1688 as registered_decks,573 AS player_count union all
  SELECT 'Main 57'  AS tournament_unique_key, 'Gold' as league,2880 as registered_decks,809 AS player_count union all
   SELECT 'Main 57'  AS tournament_unique_key, 'Silver' as league,5028 as registered_decks,1442 AS player_count union all
    SELECT 'Main 57'  AS tournament_unique_key, 'Bronze' as league,10856 as registered_decks,2653 AS player_count union all
     SELECT 'Main 57'  AS tournament_unique_key, 'Reverse' as league,4952 as registered_decks,1091 AS player_count union all 
                         SELECT 'Main 58'  AS tournament_unique_key, 'Diamond' as league,1485 as registered_decks,508 AS player_count union all
  SELECT 'Main 58'  AS tournament_unique_key, 'Gold' as league,2656 as registered_decks,752 AS player_count union all
   SELECT 'Main 58'  AS tournament_unique_key, 'Silver' as league,4866 as registered_decks,1431 AS player_count union all
    SELECT 'Main 58'  AS tournament_unique_key, 'Bronze' as league,12033 as registered_decks,2680 AS player_count union all
     SELECT 'Main 58'  AS tournament_unique_key, 'Reverse' as league,4560 as registered_decks,1025 AS player_count union all 
                              SELECT 'Main 59'  AS tournament_unique_key, 'Diamond' as league,1470 as registered_decks,505 AS player_count union all
  SELECT 'Main 59'  AS tournament_unique_key, 'Gold' as league,2738 as registered_decks,777 AS player_count union all
   SELECT 'Main 59'  AS tournament_unique_key, 'Silver' as league,4787 as registered_decks,1349 AS player_count union all
    SELECT 'Main 59'  AS tournament_unique_key, 'Bronze' as league,12132 as registered_decks,2696 AS player_count union all
     SELECT 'Main 59'  AS tournament_unique_key, 'Reverse' as league,4757 as registered_decks,946 AS player_count union all 
               SELECT 'Main 60'  AS tournament_unique_key, 'Diamond' as league,1404 as registered_decks,493 AS player_count union all
  SELECT 'Main 60'  AS tournament_unique_key, 'Gold' as league,2668 as registered_decks,757 AS player_count union all
   SELECT 'Main 60'  AS tournament_unique_key, 'Silver' as league,4727 as registered_decks,1415 AS player_count union all
    SELECT 'Main 60'  AS tournament_unique_key, 'Bronze' as league,12159 as registered_decks,2687 AS player_count union all
     SELECT 'Main 60'  AS tournament_unique_key, 'Reverse' as league,4160 as registered_decks,1034 AS player_count union all 
          SELECT 'Main 61'  AS tournament_unique_key, 'Diamond' as league,1674 as registered_decks,544 AS player_count union all
  SELECT 'Main 61'  AS tournament_unique_key, 'Gold' as league,3016 as registered_decks,816 AS player_count union all
   SELECT 'Main 61'  AS tournament_unique_key, 'Silver' as league,4848 as registered_decks,1516 AS player_count union all
    SELECT 'Main 61'  AS tournament_unique_key, 'Bronze' as league,12204 as registered_decks,2927 AS player_count union all
     SELECT 'Main 61'  AS tournament_unique_key, 'Reverse' as league,5058 as registered_decks,1116 AS player_count union all 
        SELECT 'Main 62'  AS tournament_unique_key, 'Diamond' as league,1449 as registered_decks,483 AS player_count union all
    SELECT 'Main 62'  AS tournament_unique_key, 'Gold' as league,2883 as registered_decks,771 AS player_count union all
   SELECT 'Main 62'  AS tournament_unique_key, 'Silver' as league,4943 as registered_decks,1489 AS player_count union all
    SELECT 'Main 62'  AS tournament_unique_key, 'Bronze' as league,12495 as registered_decks,2848 AS player_count union all
     SELECT 'Main 62'  AS tournament_unique_key, 'Reverse' as league,4696 as registered_decks,1039 AS player_count union all 
             SELECT 'Main 63'  AS tournament_unique_key, 'Diamond' as league,1422 as registered_decks,484 AS player_count union all
    SELECT 'Main 63'  AS tournament_unique_key, 'Gold' as league,2947 as registered_decks,794 AS player_count union all
   SELECT 'Main 63'  AS tournament_unique_key, 'Silver' as league,4744 as registered_decks,1470 AS player_count union all
    SELECT 'Main 63'  AS tournament_unique_key, 'Bronze' as league,11547 as registered_decks,2679 AS player_count union all
     SELECT 'Main 63'  AS tournament_unique_key, 'Reverse' as league,5331 as registered_decks,1237 AS player_count union all 
       SELECT 'Main 64'  AS tournament_unique_key, 'Diamond' as league,1498 as registered_decks,489 AS player_count union all
    SELECT 'Main 64'  AS tournament_unique_key, 'Gold' as league,2809 as registered_decks,809 AS player_count union all
   SELECT 'Main 64'  AS tournament_unique_key, 'Silver' as league,5126 as registered_decks,1465 AS player_count union all
    SELECT 'Main 64'  AS tournament_unique_key, 'Bronze' as league,11671 as registered_decks,2748 AS player_count union all
     SELECT 'Main 64'  AS tournament_unique_key, 'Reverse' as league,4993 as registered_decks,1125 AS player_count union all 
            SELECT 'Main 65'  AS tournament_unique_key, 'Diamond' as league,1574 as registered_decks,512 AS player_count union all
    SELECT 'Main 65'  AS tournament_unique_key, 'Gold' as league,2777 as registered_decks,779 AS player_count union all
   SELECT 'Main 65'  AS tournament_unique_key, 'Silver' as league,4897 as registered_decks,1395 AS player_count union all
    SELECT 'Main 65'  AS tournament_unique_key, 'Bronze' as league,11380 as registered_decks,2724 AS player_count union all
     SELECT 'Main 65'  AS tournament_unique_key, 'Reverse' as league,5175 as registered_decks,1161 AS player_count union all 
              SELECT 'Main 66'  AS tournament_unique_key, 'Diamond' as league,1256 as registered_decks,454 AS player_count union all
    SELECT 'Main 66'  AS tournament_unique_key, 'Gold' as league,2823 as registered_decks,753 AS player_count union all
   SELECT 'Main 66'  AS tournament_unique_key, 'Silver' as league,5130 as registered_decks,1331 AS player_count union all
    SELECT 'Main 66'  AS tournament_unique_key, 'Bronze' as league,11874 as registered_decks,2755 AS player_count union all
     SELECT 'Main 66'  AS tournament_unique_key, 'Reverse' as league,4606 as registered_decks,1048 AS player_count union all 
            SELECT 'Main 67'  AS tournament_unique_key, 'Diamond' as league,1478 as registered_decks,498 AS player_count union all
    SELECT 'Main 67'  AS tournament_unique_key, 'Gold' as league,2790 as registered_decks,752 AS player_count union all
   SELECT 'Main 67'  AS tournament_unique_key, 'Silver' as league,4722 as registered_decks,1296 AS player_count union all
    SELECT 'Main 67'  AS tournament_unique_key, 'Bronze' as league,10508 as registered_decks,2533 AS player_count union all
     SELECT 'Main 67'  AS tournament_unique_key, 'Reverse' as league,4722 as registered_decks,1150 AS player_count union all 
          SELECT 'Main 68'  AS tournament_unique_key, 'Diamond' as league,1285 as registered_decks,493 AS player_count union all
    SELECT 'Main 68'  AS tournament_unique_key, 'Gold' as league,2761 as registered_decks,700 AS player_count union all
   SELECT 'Main 68'  AS tournament_unique_key, 'Silver' as league,5018 as registered_decks,1267 AS player_count union all
    SELECT 'Main 68'  AS tournament_unique_key, 'Bronze' as league,12154 as registered_decks,2696 AS player_count union all
     SELECT 'Main 68'  AS tournament_unique_key, 'Reverse' as league,4922 as registered_decks,1189 AS player_count union all 
        SELECT 'Main 69'  AS tournament_unique_key, 'Diamond' as league,1389 as registered_decks,478 AS player_count union all
    SELECT 'Main 69'  AS tournament_unique_key, 'Gold' as league,2685 as registered_decks,703 AS player_count union all
   SELECT 'Main 69'  AS tournament_unique_key, 'Silver' as league,4699 as registered_decks,1227 AS player_count union all
    SELECT 'Main 69'  AS tournament_unique_key, 'Bronze' as league,10935 as registered_decks,2515 AS player_count union all
     SELECT 'Main 69'  AS tournament_unique_key, 'Reverse' as league,6113 as registered_decks,1226 AS player_count union all 
             SELECT 'Main 70'  AS tournament_unique_key, 'Diamond' as league,975 as registered_decks,290 AS player_count union all
     SELECT 'Main 70'  AS tournament_unique_key, 'Platinum' as league,1480 as registered_decks,493 AS player_count union all
    SELECT 'Main 70'  AS tournament_unique_key, 'Gold' as league,2429 as registered_decks,709 AS player_count union all
   SELECT 'Main 70'  AS tournament_unique_key, 'Silver' as league,4723 as registered_decks,1285 AS player_count union all
    SELECT 'Main 70'  AS tournament_unique_key, 'Bronze' as league,10938 as registered_decks,2398 AS player_count union all
     SELECT 'Main 70'  AS tournament_unique_key, 'Reverse' as league,4649 as registered_decks,1108 AS player_count union all 
        SELECT 'Main 71'  AS tournament_unique_key, 'Diamond' as league,1010 as registered_decks,282 AS player_count union all
     SELECT 'Main 71'  AS tournament_unique_key, 'Platinum' as league,1933 as registered_decks,504 AS player_count union all
    SELECT 'Main 71'  AS tournament_unique_key, 'Gold' as league,2058 as registered_decks,678 AS player_count union all
   SELECT 'Main 71'  AS tournament_unique_key, 'Silver' as league,4314 as registered_decks,1250 AS player_count union all
    SELECT 'Main 71'  AS tournament_unique_key, 'Bronze' as league,10092 as registered_decks,2364 AS player_count union all
     SELECT 'Main 71'  AS tournament_unique_key, 'Reverse' as league,4892 as registered_decks,1117 AS player_count union all 
        SELECT 'Main 72'  AS tournament_unique_key, 'Diamond' as league,992 as registered_decks,276 AS player_count union all
     SELECT 'Main 72'  AS tournament_unique_key, 'Platinum' as league,1683 as registered_decks,461 AS player_count union all
    SELECT 'Main 72'  AS tournament_unique_key, 'Gold' as league,2279 as registered_decks,720 AS player_count union all
   SELECT 'Main 72'  AS tournament_unique_key, 'Silver' as league,4478 as registered_decks,1290 AS player_count union all
    SELECT 'Main 72'  AS tournament_unique_key, 'Bronze' as league,11193 as registered_decks,2324 AS player_count union all
     SELECT 'Main 72'  AS tournament_unique_key, 'Reverse' as league,4474 as registered_decks,1045 AS player_count union all 
       SELECT 'Main 73'  AS tournament_unique_key, 'Diamond' as league,1110 as registered_decks,290 AS player_count union all
     SELECT 'Main 73'  AS tournament_unique_key, 'Platinum' as league,1833 as registered_decks,470 AS player_count union all
    SELECT 'Main 73'  AS tournament_unique_key, 'Gold' as league,2323 as registered_decks,697 AS player_count union all
   SELECT 'Main 73'  AS tournament_unique_key, 'Silver' as league,4117 as registered_decks,1186 AS player_count union all
    SELECT 'Main 73'  AS tournament_unique_key, 'Bronze' as league,10615 as registered_decks,2319 AS player_count union all
     SELECT 'Main 73'  AS tournament_unique_key, 'Reverse' as league,5144 as registered_decks,1108 AS player_count
)
select 
    concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
     gt.tournament_status,
    gt.start_timestamp,
    gt.tournament_unique_key,
    substring(gt.tournament_unique_key from position(' ' in gt.tournament_unique_key) + 1) AS tournament_number,
    gt.league,
    CASE 
        WHEN MAX(override.registered_decks) IS NOT NULL THEN
            MAX(override.registered_decks)
    ELSE 
    MAX(gt.registered_decks)
  END deck_count,
  CASE WHEN MAX(override.player_count) IS NOT NULL THEN
    MAX(override.player_count)
  ELSE 
    MAX(gt.player_count)
  END AS player_count
from
    flatten.get_tournaments gt
LEFT JOIN override
  ON gt.tournament_unique_key = override.tournament_unique_key
  and gt.league = override.league
where (gt.start_Timestamp >= NOW() at TIME zone 'UTC' - interval '60 days'
    or gt.tournament_status = 'not started'
    )
group by 1,2,3,4,5,6
order by gt.start_timestamp asc"""
league_decks_df = pd.read_sql_query(league_decks_query, conn)
cursor.close()

total_players_query = """
WITH override AS (
  SELECT 'Main 50'  AS tournament_unique_key, 4215 AS total_player_count union all 
   SELECT 'Main 51'  AS tournament_unique_key, 4195 AS total_player_count union all 
  SELECT 'Main 52'  AS tournament_unique_key, 3952 AS total_player_count union all
  SELECT 'Main 53'  AS tournament_unique_key, 3919 AS total_player_count union all
  SELECT 'Main 54'  AS tournament_unique_key, 3937 AS total_player_count union all
  SELECT 'Main 55'  AS tournament_unique_key, 3729 AS total_player_count  union all
   SELECT 'Main 56'  AS tournament_unique_key, 3638 AS total_player_count union all
     SELECT 'Main 57'  AS tournament_unique_key, 3442 AS total_player_count union all 
          SELECT 'Main 58'  AS tournament_unique_key, 3425 AS total_player_count union all 
             SELECT 'Main 59'  AS tournament_unique_key, 3369 AS total_player_count union all 
              SELECT 'Main 60'  AS tournament_unique_key, 3404 AS total_player_count union all
               SELECT 'Main 61'  AS tournament_unique_key, 3698 AS total_player_count  union all
                SELECT 'Main 62'  AS tournament_unique_key, 3614 AS total_player_count  union all 
                SELECT 'Main 63'  AS tournament_unique_key, 3549 AS total_player_count  union all 
                   SELECT 'Main 64'  AS tournament_unique_key, 3583 AS total_player_count union all 
                        SELECT 'Main 65'  AS tournament_unique_key, 3450 AS total_player_count union all 
     SELECT 'Main 66'  AS tournament_unique_key, 3441 AS total_player_count  union all 
        SELECT 'Main 67'  AS tournament_unique_key, 3301 AS total_player_count union all 
          SELECT 'Main 68'  AS tournament_unique_key, 3419 AS total_player_count union all 
            SELECT 'Main 69'  AS tournament_unique_key, 3267 AS total_player_count  union all 
               SELECT 'Main 70'  AS tournament_unique_key, 3262 AS total_player_count  union all 
                          SELECT 'Main 71'  AS tournament_unique_key, 3201 AS total_player_count  union all 
                                    SELECT 'Main 72'  AS tournament_unique_key, 3189 AS total_player_count union all 
                                      SELECT 'Main 73'  AS tournament_unique_key, 3097 AS total_player_count 
)
SELECT 
    CONCAT(TO_CHAR(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key) AS tournament,
    gt.start_timestamp,
    gt.tournament_unique_key,
    SUBSTRING(gt.tournament_unique_key FROM POSITION(' ' IN gt.tournament_unique_key) + 1) AS tournament_number,
    CASE WHEN MAX(override.total_player_count) IS NOT NULL THEN
        MAX(override.total_player_count)
    ELSE 
        COUNT(DISTINCT gtpp.player_id)
    END AS player_count
FROM
    flatten.get_tournaments gt
JOIN flatten.tournament_players gtpp
    ON gt.tournament_id = gtpp.tournament_id
LEFT JOIN override
    ON gt.tournament_unique_key = override.tournament_unique_key
WHERE gt.start_Timestamp >= NOW() AT TIME ZONE 'UTC' - INTERVAL '60 days'
GROUP BY 1,2,3,4
ORDER BY gt.start_timestamp ASC
"""

total_players_df = pd.read_sql_query(total_players_query, conn)
cursor.close()


card_stars_query = f"""
select concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
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


rarity_query = f"""
WITH override AS (
  SELECT 'Main 52'  AS tournament_unique_key, 'legendary' as rarity,358 AS card_count union all
  SELECT 'Main 52'  AS tournament_unique_key, 'epic' as rarity,3174 AS card_count union all
  SELECT 'Main 52'  AS tournament_unique_key, 'rare' as rarity,20600 AS card_count union all
  SELECT 'Main 52'  AS tournament_unique_key, 'common' as rarity,104088 AS card_count UNION ALL
    SELECT 'Main 51'  AS tournament_unique_key, 'legendary' as rarity,357 AS card_count union all
  SELECT 'Main 51'  AS tournament_unique_key, 'epic' as rarity,3155 AS card_count union all
  SELECT 'Main 51'  AS tournament_unique_key, 'rare' as rarity,20511 AS card_count union all
  SELECT 'Main 52'  AS tournament_unique_key, 'common' as rarity,101262 AS card_count UNION ALL
  SELECT 'Main 53'  AS tournament_unique_key, 'legendary' as rarity,337 AS card_count union all
  SELECT 'Main 53'  AS tournament_unique_key, 'epic' as rarity,3170 AS card_count union all
  SELECT 'Main 53'  AS tournament_unique_key, 'rare' as rarity,20600 AS card_count union all
  SELECT 'Main 53'  AS tournament_unique_key, 'common' as rarity,100028 AS card_count union all
  SELECT 'Main 54'  AS tournament_unique_key, 'legendary' as rarity,378 AS card_count union all
  SELECT 'Main 54'  AS tournament_unique_key, 'epic' as rarity,3298 AS card_count union all
  SELECT 'Main 54'  AS tournament_unique_key, 'rare' as rarity,21815 AS card_count union all
  SELECT 'Main 54'  AS tournament_unique_key, 'common' as rarity,105109 AS card_count union all
    SELECT 'Main 55'  AS tournament_unique_key, 'legendary' as rarity,349 AS card_count union all
  SELECT 'Main 55'  AS tournament_unique_key, 'epic' as rarity,3185 AS card_count union all
  SELECT 'Main 55'  AS tournament_unique_key, 'rare' as rarity,20942 AS card_count union all
  SELECT 'Main 55'  AS tournament_unique_key, 'common' as rarity,98919 AS card_count union all
   SELECT 'Main 56'  AS tournament_unique_key, 'legendary' as rarity,345 AS card_count union all
  SELECT 'Main 56'  AS tournament_unique_key, 'epic' as rarity,3233 AS card_count union all
  SELECT 'Main 56'  AS tournament_unique_key, 'rare' as rarity,21207 AS card_count union all
  SELECT 'Main 56'  AS tournament_unique_key, 'common' as rarity,101315 AS card_count union all 
     SELECT 'Main 57'  AS tournament_unique_key, 'legendary' as rarity,362 AS card_count union all
  SELECT 'Main 57'  AS tournament_unique_key, 'epic' as rarity,3309 AS card_count union all
  SELECT 'Main 57'  AS tournament_unique_key, 'rare' as rarity,21390 AS card_count union all
  SELECT 'Main 57'  AS tournament_unique_key, 'common' as rarity,101959 AS card_count union all 
       SELECT 'Main 58'  AS tournament_unique_key, 'legendary' as rarity,337 AS card_count union all
  SELECT 'Main 58'  AS tournament_unique_key, 'epic' as rarity,3241 AS card_count union all
  SELECT 'Main 58'  AS tournament_unique_key, 'rare' as rarity,20980 AS card_count union all
  SELECT 'Main 58'  AS tournament_unique_key, 'common' as rarity,103442 AS card_count union all 
        SELECT 'Main 59'  AS tournament_unique_key, 'legendary' as rarity,345 AS card_count union all
  SELECT 'Main 59'  AS tournament_unique_key, 'epic' as rarity,3275 AS card_count union all
  SELECT 'Main 59'  AS tournament_unique_key, 'rare' as rarity,21152 AS card_count union all
  SELECT 'Main 59'  AS tournament_unique_key, 'common' as rarity,104648 AS card_count union all
      SELECT 'Main 60'  AS tournament_unique_key, 'legendary' as rarity,347 AS card_count union all
  SELECT 'Main 60'  AS tournament_unique_key, 'epic' as rarity,3274 AS card_count union all
  SELECT 'Main 60'  AS tournament_unique_key, 'rare' as rarity,21292 AS card_count union all
  SELECT 'Main 60'  AS tournament_unique_key, 'common' as rarity,100677 AS card_count  union all 
        SELECT 'Main 61'  AS tournament_unique_key, 'legendary' as rarity,334 AS card_count union all
  SELECT 'Main 61'  AS tournament_unique_key, 'epic' as rarity,3387 AS card_count union all
  SELECT 'Main 61'  AS tournament_unique_key, 'rare' as rarity,22057 AS card_count union all
  SELECT 'Main 61'  AS tournament_unique_key, 'common' as rarity,108222 AS card_count union all 
          SELECT 'Main 62'  AS tournament_unique_key, 'legendary' as rarity,359 AS card_count union all
  SELECT 'Main 62'  AS tournament_unique_key, 'epic' as rarity,3271 AS card_count union all
  SELECT 'Main 62'  AS tournament_unique_key, 'rare' as rarity,21758 AS card_count union all
  SELECT 'Main 62'  AS tournament_unique_key, 'common' as rarity,106942 AS card_count  union all
          SELECT 'Main 63'  AS tournament_unique_key, 'legendary' as rarity,369 AS card_count union all
  SELECT 'Main 63'  AS tournament_unique_key, 'epic' as rarity,3378 AS card_count union all
  SELECT 'Main 63'  AS tournament_unique_key, 'rare' as rarity,21957 AS card_count union all
  SELECT 'Main 63'  AS tournament_unique_key, 'common' as rarity,104251 AS card_count union all 
      SELECT 'Main 64'  AS tournament_unique_key, 'legendary' as rarity,366 AS card_count union all
  SELECT 'Main 64'  AS tournament_unique_key, 'epic' as rarity,3393 AS card_count union all
  SELECT 'Main 64'  AS tournament_unique_key, 'rare' as rarity,22513 AS card_count union all
  SELECT 'Main 64'  AS tournament_unique_key, 'common' as rarity,104213 AS card_count union all 
        SELECT 'Main 65'  AS tournament_unique_key, 'legendary' as rarity,367 AS card_count union all
  SELECT 'Main 65'  AS tournament_unique_key, 'epic' as rarity,3404 AS card_count union all
  SELECT 'Main 65'  AS tournament_unique_key, 'rare' as rarity,22400 AS card_count union all
  SELECT 'Main 65'  AS tournament_unique_key, 'common' as rarity,102844 AS card_count  union all 
          SELECT 'Main 66'  AS tournament_unique_key, 'legendary' as rarity,375 AS card_count union all
  SELECT 'Main 66'  AS tournament_unique_key, 'epic' as rarity,3454 AS card_count union all
  SELECT 'Main 66'  AS tournament_unique_key, 'rare' as rarity,22422 AS card_count union all
  SELECT 'Main 66'  AS tournament_unique_key, 'common' as rarity,102194 AS card_count  union all 
       SELECT 'Main 67'  AS tournament_unique_key, 'legendary' as rarity,349 AS card_count union all
  SELECT 'Main 67'  AS tournament_unique_key, 'epic' as rarity,3437 AS card_count union all
  SELECT 'Main 67'  AS tournament_unique_key, 'rare' as rarity,21986 AS card_count union all
  SELECT 'Main 67'  AS tournament_unique_key, 'common' as rarity,101688 AS card_count union all 
         SELECT 'Main 68'  AS tournament_unique_key, 'legendary' as rarity,339 AS card_count union all
  SELECT 'Main 68'  AS tournament_unique_key, 'epic' as rarity,3473 AS card_count union all
  SELECT 'Main 68'  AS tournament_unique_key, 'rare' as rarity,22229 AS card_count union all
  SELECT 'Main 68'  AS tournament_unique_key, 'common' as rarity,104659 AS card_count union all 
         SELECT 'Main 69'  AS tournament_unique_key, 'legendary' as rarity,341 AS card_count union all
  SELECT 'Main 69'  AS tournament_unique_key, 'epic' as rarity,3499 AS card_count union all
  SELECT 'Main 69'  AS tournament_unique_key, 'rare' as rarity,21985 AS card_count union all
  SELECT 'Main 69'  AS tournament_unique_key, 'common' as rarity,103280 AS card_count  union all
          SELECT 'Main 70'  AS tournament_unique_key, 'legendary' as rarity,389 AS card_count union all
  SELECT 'Main 70'  AS tournament_unique_key, 'epic' as rarity,3554 AS card_count union all
  SELECT 'Main 70'  AS tournament_unique_key, 'rare' as rarity,22668 AS card_count union all
  SELECT 'Main 70'  AS tournament_unique_key, 'common' as rarity,99350 AS card_count  union all 
            SELECT 'Main 71'  AS tournament_unique_key, 'legendary' as rarity,408 AS card_count union all
  SELECT 'Main 71'  AS tournament_unique_key, 'epic' as rarity,3551 AS card_count union all
  SELECT 'Main 71'  AS tournament_unique_key, 'rare' as rarity,22273 AS card_count union all
  SELECT 'Main 71'  AS tournament_unique_key, 'common' as rarity,95263 AS card_count  union all 
              SELECT 'Main 72'  AS tournament_unique_key, 'legendary' as rarity,399 AS card_count union all
  SELECT 'Main 72'  AS tournament_unique_key, 'epic' as rarity,3526 AS card_count union all
  SELECT 'Main 72'  AS tournament_unique_key, 'rare' as rarity,22510 AS card_count union all
  SELECT 'Main 72'  AS tournament_unique_key, 'common' as rarity,99060 AS card_count  union all 
              SELECT 'Main 73'  AS tournament_unique_key, 'legendary' as rarity,394 AS card_count union all
  SELECT 'Main 73'  AS tournament_unique_key, 'epic' as rarity,3537 AS card_count union all
  SELECT 'Main 73'  AS tournament_unique_key, 'rare' as rarity,22468 AS card_count union all
  SELECT 'Main 73'  AS tournament_unique_key, 'common' as rarity,99311 AS card_count  
)
select concat(to_char(gt.start_timestamp, 'MM-DD'),' | ', gt.tournament_unique_key ) as tournament,
gt.start_timestamp,
 gt.tournament_unique_key,
    t.hero_rarity,
     CASE WHEN MAX(override.card_count) IS NOT NULL THEN
        MAX(override.card_count)
    ELSE 
        count(*) 
    END as card_count
from agg.tournamentownership t 
join   flatten.get_tournaments gt
    on t.tournament_id  = gt.tournament_id 
left join override 
    on t.tournament_unique_key = override.tournament_unique_key
    and t.hero_rarity = override.rarity
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
and gt.tournament_seq_nbr <= 8
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
            'tournament_status': row['tournament_status'],
            'tournament_number': row['tournament_number'],
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



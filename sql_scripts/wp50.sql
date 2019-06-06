SELECT match_id,
       killer_name AS player_name,
       victim_name AS favorite_victim_name,
       kill_count
FROM (SELECT match_id,
             killer_name,
             victim_name,
             count(victim_name) AS kill_count,
             row_number()
             OVER (
                 PARTITION BY match_id, killer_name
                 ORDER BY COUNT(victim_name) DESC, min(frag_time)
                 )              AS pos
      FROM match_frag
      WHERE victim_name IS NOT NULL
      GROUP BY match_id, killer_name, victim_name
      ORDER BY match_id, killer_name, kill_count DESC
     ) AS ss
WHERE pos = 1;
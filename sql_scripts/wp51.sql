SELECT match_id,
       victim_name AS player_name,
       killer_name AS worst_enemy_name,
       kill_count
FROM (SELECT match_id,
             killer_name,
             victim_name,
             count(killer_name) AS kill_count,
             row_number()
             OVER (
                 PARTITION BY match_id, victim_name
                 ORDER BY count(killer_name) DESC, min(frag_time)
                 )              AS pos
      FROM match_frag
      WHERE victim_name IS NOT NULL
      GROUP BY match_id, victim_name, killer_name
      ORDER BY match_id, victim_name, kill_count DESC
     ) AS ss
WHERE pos = 1;
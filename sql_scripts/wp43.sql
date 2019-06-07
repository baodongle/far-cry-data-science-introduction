SELECT match.match_id,
       match.start_time,
       match.end_time,
       T.player_count,
       T.kill_suicide_count
FROM match
         JOIN
     (
         SELECT T1.match_id,
                T3.player_count,
                T1.kill_suicide_count
         FROM (
                  SELECT match_id,
                         COUNT(killer_name) AS kill_suicide_count
                  FROM match_frag
                  GROUP BY match_id
              ) AS T1
                  INNER JOIN
              (
                  SELECT match_id,
                         COUNT(player_name) AS player_count
                  FROM (
                           SELECT DISTINCT match_id,
                                           killer_name AS player_name
                           FROM match_frag
                           UNION
                           SELECT DISTINCT match_id,
                                           victim_name AS player_name
                           FROM match_frag
                           WHERE victim_name IS NOT NULL
                       ) AS T2
                  GROUP BY match_id
              ) AS T3
              ON T1.match_id = T3.match_id
     ) AS T
     ON match.match_id = T.match_id
ORDER BY match.start_time;
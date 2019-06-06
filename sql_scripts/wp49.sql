SELECT match_id, killer_name, count(DISTINCT weapon_code) AS weapon_count
FROM match_frag
GROUP BY match_id, killer_name
ORDER BY match_id, weapon_count DESC;
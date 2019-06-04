-- Calculate and Order the Number of Kills per Player and per Match
select match_id, killer_name as player_name, count(killer_name) as kill_count
from match_frag
group by match_id, killer_name
order by match_id, kill_count desc;
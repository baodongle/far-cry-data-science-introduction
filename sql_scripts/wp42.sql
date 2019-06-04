-- Calculate and Order the Number of Deaths per Player and per Match
select match_id, killer_name as player_name, count(victim_name) as death_count
from match_frag
group by match_id, killer_name
order by match_id, death_count desc;
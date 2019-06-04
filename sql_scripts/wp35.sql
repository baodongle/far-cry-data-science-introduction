-- Calculate the Number of Kills
select count(killer_name) as kill_count
from match_frag
where victim_name is not null;
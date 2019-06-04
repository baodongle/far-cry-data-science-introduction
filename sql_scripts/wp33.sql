-- Calculate the number of Kills and Suicides
select count(killer_name) as kill_suicide_count
from match_frag;
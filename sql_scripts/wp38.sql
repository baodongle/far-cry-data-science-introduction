-- Calculate and Order the Number of Kills and Suicides per Match
select match_id, count(killer_name) as kill_suicide_count
from match_frag
group by match_id
order by kill_suicide_count desc;
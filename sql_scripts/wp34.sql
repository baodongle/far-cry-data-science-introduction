-- Calculate the Number of Suicides
select count(killer_name) as suicide_count
from match_frag
where victim_name is null;
-- Calculate and Order the Number of Suicides per Match
select match_id, count(killer_name) as suicide_count
from match_frag
where victim_name is null
group by match_id
order by suicide_count;
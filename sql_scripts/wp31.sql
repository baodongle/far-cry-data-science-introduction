-- Order the List of Killer Names
select distinct killer_name
from match_frag
where victim_name is not not null
order by killer_name;
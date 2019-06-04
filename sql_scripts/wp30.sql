-- Select distinct Killer Names
select distinct killer_name
from match_frag
where victim_name is not null;
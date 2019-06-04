-- Calculate the Number of Deaths per Player and Per Match
select match_id,
       victim_name        as player_name,
       0                  as kill_count,
       0                  as suicide_count,
       count(victim_name) as death_count
from match_frag
where victim_name is not null
group by match_id, victim_name;
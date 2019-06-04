-- Calculate and Order the Total Number of Kills per Player
select killer_name as player_name, count(killer_name) as kill_count
from match_frag
group by killer_name
order by kill_count desc, killer_name;
-- Select Matches and Calculate the Number of Players and the Number of Kills and Suicides
select match.match_id,
       start_time,
       end_time,
       count(distinct killer_name) as player_count,
       count(killer_name)          as kill_suicide_count
from match
         join match_frag as mf on match.match_id = mf.match_id
group by match.match_id
order by start_time;